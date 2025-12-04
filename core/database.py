# core/database.py
import psycopg2
import psycopg2.extensions
from psycopg2 import sql
import hashlib
from datetime import datetime
import io
import streamlit as st
import json
import traceback

class ContratosManager:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
        psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)
    
    def _get_connection(self):
        conn = psycopg2.connect(self.connection_string)
        conn.autocommit = False
        return conn
    
    def init_db(self):
        """Inicializar la base de datos con TODOS los campos PEMEX"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contratos_pemex (
                    id BIGSERIAL PRIMARY KEY,
                    area VARCHAR(500) NOT NULL DEFAULT 'SUBDIRECCIÓN DE PRODUCCIÓN REGIÓN NORTE GERENCIA DE MANTENIMIENTO CONFIABILIDAD Y CONSTRUCCIÓN',
                    numero_contrato VARCHAR(100) UNIQUE NOT NULL,
                    contratista VARCHAR(300) NOT NULL,
                    monto_contrato VARCHAR(100),
                    plazo_dias VARCHAR(50),
                    descripcion TEXT,
                    anexos JSONB,
                    
                    -- Archivo original
                    lo_oid OID NOT NULL,
                    nombre_archivo VARCHAR(300) NOT NULL,
                    tipo_archivo VARCHAR(50),
                    tamaño_bytes BIGINT NOT NULL,
                    hash_sha256 VARCHAR(64) NOT NULL,
                    
                    -- Metadatos del sistema
                    fecha_subida TIMESTAMPTZ DEFAULT NOW(),
                    usuario_subio VARCHAR(100) DEFAULT 'sistema',
                    procesado BOOLEAN DEFAULT TRUE,
                    
                    CONSTRAINT check_tamaño_positivo CHECK (tamaño_bytes > 0)
                )
            """)
            
            # Índices
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contratos_numero ON contratos_pemex(numero_contrato)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contratos_contratista ON contratos_pemex(contratista)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contratos_fecha ON contratos_pemex(fecha_subida)")
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"❌ Error inicializando BD: {str(e)}")
        finally:
            conn.close()
    
    def calcular_hash(self, file_bytes):
        return hashlib.sha256(file_bytes).hexdigest()

    def _safe_string(self, value):
        """Conversión 100% segura a string - SOLUCIÓN DEFINITIVA"""
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, dict)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except:
                return str(value)
        else:
            return str(value)

    def _debug_datos(self, datos, titulo):
        """Debugging extensivo"""
        print(f"🔍 {titulo}:")
        for key, value in datos.items():
            print(f"  {key}: {repr(value)} (tipo: {type(value).__name__})")

    def guardar_contrato_pemex(self, archivo, datos_extraidos, usuario="sistema"):
        """
        Guardar contrato en PostgreSQL - VERSIÓN CORREGIDA
        """
        conn = self._get_connection()
        try:
            self._debug_datos(datos_extraidos, "DEBUG DATOS CRUDOS")
            
            file_bytes = archivo.getvalue()
            file_hash = self.calcular_hash(file_bytes)
            
            # CORRECCIÓN: Large Object con None en lugar de True
            lo_oid = conn.lobject(0, 'wb', 0, None)  # ← CORREGIDO AQUÍ
            
            # Escribir archivo en chunks
            chunk_size = 1024 * 1024
            with io.BytesIO(file_bytes) as file_stream:
                while True:
                    chunk = file_stream.read(chunk_size)
                    if not chunk:
                        break
                    lo_oid.write(chunk)
            
            # CONVERSIÓN 100% SEGURA
            contrato = self._safe_string(datos_extraidos.get('contrato', ''))
            contratista = self._safe_string(datos_extraidos.get('contratista', ''))
            monto = self._safe_string(datos_extraidos.get('monto', ''))
            
            # SOLUCIÓN DEFINITIVA PARA PLAZO
            plazo_original = datos_extraidos.get('plazo', '')
            print(f"🚨 PLAZO ORIGINAL: {repr(plazo_original)} (tipo: {type(plazo_original).__name__})")
            
            plazo = self._safe_string(plazo_original)
            print(f"🚨 PLAZO CONVERTIDO: {repr(plazo)} (tipo: {type(plazo).__name__})")
            
            if not isinstance(plazo, str):
                plazo = str(plazo) if plazo is not None else ""
                print(f"🚨 PLAZO FORZADO: {repr(plazo)}")
            
            objeto = self._safe_string(datos_extraidos.get('objeto', ''))
            anexos = json.dumps(datos_extraidos.get('anexos', []), ensure_ascii=False)
            
            # Datos finales para debug
            datos_finales = {
                'contrato': contrato,
                'contratista': contratista,
                'monto': monto,
                'plazo': plazo,
                'objeto': objeto
            }
            self._debug_datos(datos_finales, "DATOS FINALES PARA POSTGRESQL")
            
            # Insertar en PostgreSQL
            cur = conn.cursor()
            query = sql.SQL("""
                INSERT INTO contratos_pemex (
                    numero_contrato, contratista, monto_contrato, 
                    plazo_dias, descripcion, anexos,
                    lo_oid, nombre_archivo, tipo_archivo, tamaño_bytes, hash_sha256, usuario_subio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """)
            
            cur.execute(query, (
                contrato, contratista, monto, plazo, objeto, anexos,
                lo_oid.oid, archivo.name, getattr(archivo, 'type', 'application/pdf'),
                len(file_bytes), file_hash, usuario
            ))
            
            contrato_id = cur.fetchone()[0]
            conn.commit()
            
            print(f"✅ CONTRATO GUARDADO EN POSTGRESQL - ID: {contrato_id}")
            return contrato_id
            
        except psycopg2.IntegrityError:
            conn.rollback()
            raise Exception("❌ Ya existe un contrato con ese número")
        except Exception as e:
            conn.rollback()
            print(f"🔴 ERROR DETALLADO: {traceback.format_exc()}")
            raise Exception(f"❌ Error guardando contrato: {str(e)}")
        finally:
            conn.close()

    def guardar_contrato_completo(self, archivos_data, datos_contrato, usuario="sistema"):
        """
        Guardar contrato completo - SOLO POSTGRESQL
        """
        try:
            self._debug_datos(datos_contrato, "DATOS CONTRATO ORIGINAL")
            
            # Limpiar datos
            datos_limpios = {}
            for key, value in datos_contrato.items():
                datos_limpios[key] = self._safe_string(value)
            
            self._debug_datos(datos_limpios, "DATOS LIMPIOS")
            
            # Guardar en PostgreSQL
            archivo_principal = archivos_data['principal']
            contrato_id = self.guardar_contrato_pemex(archivo_principal, datos_limpios, usuario)
            
            if contrato_id:
                st.success(f"🗄️ **Contrato guardado en PostgreSQL** (ID: {contrato_id})")
                return contrato_id
            else:
                raise Exception("No se pudo obtener ID del contrato")
                
        except Exception as e:
            st.error(f"❌ Error guardando en PostgreSQL: {str(e)}")
            raise Exception(f"Error guardando contrato: {str(e)}")
    
    def buscar_contratos_pemex(self, filtros=None):
        """Búsqueda en PostgreSQL"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            where_conditions = []
            params = []
            
            if filtros:
                if 'numero_contrato' in filtros and filtros['numero_contrato']:
                    where_conditions.append("numero_contrato ILIKE %s")
                    params.append(f"%{filtros['numero_contrato']}%")
                if 'contratista' in filtros and filtros['contratista']:
                    where_conditions.append("contratista ILIKE %s")
                    params.append(f"%{filtros['contratista']}%")
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            query = f"""
                SELECT id, area, numero_contrato, contratista, monto_contrato, 
                       plazo_dias, descripcion, anexos, nombre_archivo, tipo_archivo,
                       fecha_subida, tamaño_bytes, usuario_subio
                FROM contratos_pemex
                WHERE {where_clause}
                ORDER BY fecha_subida DESC
            """
            
            cur.execute(query, params)
            resultados = cur.fetchall()
            
            columnas = [desc[0] for desc in cur.description]
            contratos = [dict(zip(columnas, fila)) for fila in resultados]
            
            # Convertir JSON de anexos
            for contrato in contratos:
                if contrato.get('anexos'):
                    try:
                        contrato['anexos'] = json.loads(contrato['anexos'])
                    except:
                        contrato['anexos'] = []
            
            return contratos
            
        except Exception as e:
            raise Exception(f"❌ Error buscando contratos: {str(e)}")
        finally:
            conn.close()
    
    def obtener_contrato_por_id(self, contrato_id):
        """Obtener contrato completo por ID"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT id, numero_contrato, lo_oid, nombre_archivo, tipo_archivo,
                       tamaño_bytes, hash_sha256
                FROM contratos_pemex
                WHERE id = %s
            """, (contrato_id,))
            
            resultado = cur.fetchone()
            if not resultado:
                return None
            
            columnas = [desc[0] for desc in cur.description]
            metadata = dict(zip(columnas, resultado))
            
            # CORRECCIÓN: Large Object con parámetros correctos
            lo_oid = metadata['lo_oid']
            large_obj = conn.lobject(lo_oid, 'rb', 0, None)  # ← CORREGIDO AQUÍ
            
            chunks = []
            chunk_size = 1024 * 1024
            while True:
                chunk = large_obj.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
            
            contenido = b''.join(chunks)
            
            return {
                'metadata': metadata,
                'contenido': contenido
            }
            
        except Exception as e:
            raise Exception(f"❌ Error obteniendo contrato: {str(e)}")
        finally:
            conn.close()
    
    def eliminar_contrato(self, contrato_id):
        """Eliminar contrato de PostgreSQL"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Obtener OID antes de eliminar
            cur.execute("SELECT lo_oid FROM contratos_pemex WHERE id = %s", (contrato_id,))
            resultado = cur.fetchone()
            
            if resultado:
                lo_oid = resultado[0]
                
                # Eliminar de la tabla
                cur.execute("DELETE FROM contratos_pemex WHERE id = %s", (contrato_id,))
                
                # Eliminar Large Object
                try:
                    large_obj = conn.lobject(lo_oid)
                    large_obj.unlink()
                except:
                    pass
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"❌ Error eliminando contrato: {str(e)}")
        finally:
            conn.close()
    
    def obtener_estadisticas_pemex(self):
        """Obtener estadísticas de PostgreSQL"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    COUNT(*) as total_contratos,
                    COALESCE(SUM(tamaño_bytes), 0) as total_bytes,
                    COUNT(DISTINCT contratista) as contratistas_unicos,
                    MIN(fecha_subida) as fecha_mas_antigua,
                    MAX(fecha_subida) as fecha_mas_reciente
                FROM contratos_pemex
            """)
            
            stats = dict(zip(['total_contratos', 'total_bytes', 'contratistas_unicos', 
                            'fecha_mas_antigua', 'fecha_mas_reciente'], 
                           cur.fetchone()))
            
            # Formatear fechas
            for key in ['fecha_mas_antigua', 'fecha_mas_reciente']:
                if stats[key]:
                    stats[key] = stats[key].strftime('%Y-%m-%d')
            
            return stats
            
        except Exception as e:
            raise Exception(f"❌ Error obteniendo estadísticas: {str(e)}")
        finally:
            conn.close()

    # ============================================
    # MÉTODOS NUEVOS CORREGIDOS PARA ARCHIVOS
    # ============================================
    
    def verificar_tabla_archivos(self):
        """Verificar y crear la tabla archivos_pemex si no existe"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            # Verificar si la tabla existe
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'archivos_pemex'
                )
            """)
            
            tabla_existe = cur.fetchone()[0]
            
            if not tabla_existe:
                print("📁 Creando tabla archivos_pemex...")
                cur.execute("""
                    CREATE TABLE archivos_pemex (
                        id BIGSERIAL PRIMARY KEY,
                        contrato_id BIGINT NOT NULL REFERENCES contratos_pemex(id) ON DELETE CASCADE,
                        categoria VARCHAR(50) NOT NULL,
                        tipo_archivo VARCHAR(50),
                        lo_oid OID NOT NULL,
                        nombre_archivo VARCHAR(300) NOT NULL,
                        tamaño_bytes BIGINT NOT NULL,
                        hash_sha256 VARCHAR(64) NOT NULL,
                        fecha_subida TIMESTAMPTZ DEFAULT NOW(),
                        usuario_subio VARCHAR(100) DEFAULT 'sistema',
                        CONSTRAINT check_tamaño_archivo CHECK (tamaño_bytes > 0)
                    )
                """)
                
                # Crear índices
                cur.execute("CREATE INDEX idx_archivos_contrato_id ON archivos_pemex(contrato_id)")
                cur.execute("CREATE INDEX idx_archivos_categoria ON archivos_pemex(categoria)")
                cur.execute("CREATE INDEX idx_archivos_fecha ON archivos_pemex(fecha_subida)")
                
                conn.commit()
                print("✅ Tabla archivos_pemex creada exitosamente")
            
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error verificando tabla archivos: {str(e)}")
            return False
        finally:
            conn.close()

    def guardar_archivo_completo(self, contrato_id, archivo, categoria, tipo_archivo, usuario="sistema"):
        """
        GUARDAR ARCHIVO INDIVIDUAL - VERSIÓN MEJORADA Y CORREGIDA
        """
        conn = self._get_connection()
        try:
            # Asegurar que la tabla existe
            self.verificar_tabla_archivos()
            
            # Manejar diferentes tipos de entrada
            if hasattr(archivo, 'read'):
                # Es un objeto tipo archivo (de Streamlit)
                file_bytes = archivo.read()
                file_name = archivo.name
            elif isinstance(archivo, bytes):
                # Son bytes directos
                file_bytes = archivo
                file_name = f"archivo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            elif isinstance(archivo, str):
                # Es una ruta de archivo
                with open(archivo, 'rb') as f:
                    file_bytes = f.read()
                file_name = archivo.split('/')[-1]
            else:
                raise ValueError("Tipo de archivo no soportado")
            
            file_hash = self.calcular_hash(file_bytes)
            
            # Verificar si ya existe un archivo con el mismo nombre en la misma categoría
            if self.validar_archivo(contrato_id, categoria, file_name):
                # Generar nombre único
                import uuid
                nombre_base = file_name.rsplit('.', 1)[0] if '.' in file_name else file_name
                extension = file_name.split('.')[-1] if '.' in file_name else ''
                file_name = f"{nombre_base}_{uuid.uuid4().hex[:8]}.{extension}"
            
            # Crear Large Object
            lo_oid = conn.lobject(0, 'wb', 0, None)
            
            # Escribir en chunks
            chunk_size = 1024 * 1024
            with io.BytesIO(file_bytes) as file_stream:
                while True:
                    chunk = file_stream.read(chunk_size)
                    if not chunk:
                        break
                    lo_oid.write(chunk)
            
            # Insertar archivo
            cur = conn.cursor()
            query = sql.SQL("""
                INSERT INTO archivos_pemex (
                    contrato_id, categoria, tipo_archivo,
                    lo_oid, nombre_archivo, tamaño_bytes, hash_sha256, usuario_subio
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """)
            
            cur.execute(query, (
                contrato_id, categoria, tipo_archivo,
                lo_oid.oid, file_name, len(file_bytes), file_hash, usuario
            ))
            
            archivo_id = cur.fetchone()[0]
            conn.commit()
            
            print(f"✅ Archivo guardado: {file_name} | ID: {archivo_id} | Categoría: {categoria}")
            return archivo_id
            
        except Exception as e:
            conn.rollback()
            print(f"❌ ERROR guardando archivo: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Error guardando archivo: {str(e)}")
        finally:
            conn.close()

    def guardar_archivo_streamlit(self, contrato_id, archivo_streamlit, categoria, usuario="sistema"):
        """
        VERSIÓN ESPECÍFICA para archivos de Streamlit
        """
        try:
            # Verificar tabla primero
            self.verificar_tabla_archivos()
            
            # Leer el archivo de Streamlit
            archivo_bytes = archivo_streamlit.read()
            
            # Volver al inicio
            archivo_streamlit.seek(0)
            
            # Usar el método existente pero adaptado
            return self.guardar_archivo_completo(
                contrato_id=contrato_id,
                archivo=archivo_bytes,  # Enviar bytes, no el objeto streamlit
                categoria=categoria,
                tipo_archivo=getattr(archivo_streamlit, 'type', 'application/octet-stream'),
                usuario=usuario
            )
            
        except Exception as e:
            raise Exception(f"Error guardando archivo Streamlit: {str(e)}")

    def obtener_archivos(self, contrato_id, categoria=None):
        """
        OBTENER ARCHIVOS POR CONTRATO Y CATEGORÍA - VERSIÓN CORREGIDA
        """
        conn = self._get_connection()
        try:
            # Verificar tabla primero
            self.verificar_tabla_archivos()
            
            cur = conn.cursor()
            
            if categoria:
                cur.execute("""
                    SELECT id, contrato_id, categoria, tipo_archivo,
                           lo_oid, nombre_archivo, tamaño_bytes, hash_sha256,
                           fecha_subida, usuario_subio
                    FROM archivos_pemex
                    WHERE contrato_id = %s AND categoria = %s
                    ORDER BY fecha_subida DESC
                """, (contrato_id, categoria))
            else:
                cur.execute("""
                    SELECT id, contrato_id, categoria, tipo_archivo,
                           lo_oid, nombre_archivo, tamaño_bytes, hash_sha256,
                           fecha_subida, usuario_subio
                    FROM archivos_pemex
                    WHERE contrato_id = %s
                    ORDER BY categoria, fecha_subida DESC
                """, (contrato_id,))
            
            resultados = cur.fetchall()
            
            if not resultados:
                return []
            
            columnas = [desc[0] for desc in cur.description]
            archivos = []
            
            for fila in resultados:
                metadata = dict(zip(columnas, fila))
                
                # Obtener contenido
                lo_oid = metadata['lo_oid']
                try:
                    large_obj = conn.lobject(lo_oid, 'rb', 0, None)
                    
                    chunks = []
                    chunk_size = 1024 * 1024
                    while True:
                        chunk = large_obj.read(chunk_size)
                        if not chunk:
                            break
                        chunks.append(chunk)
                    
                    contenido = b''.join(chunks)
                    
                    archivo_completo = {
                        'id': metadata['id'],
                        'contrato_id': metadata['contrato_id'],
                        'categoria': metadata['categoria'],
                        'nombre_archivo': metadata['nombre_archivo'],
                        'tipo_archivo': metadata['tipo_archivo'],
                        'tamaño_bytes': metadata['tamaño_bytes'],
                        'hash_sha256': metadata['hash_sha256'],
                        'fecha_subida': metadata['fecha_subida'],
                        'usuario_subio': metadata['usuario_subio'],
                        'contenido': contenido
                    }
                    
                    archivos.append(archivo_completo)
                    
                except Exception as e:
                    print(f"⚠️ Error obteniendo contenido del archivo {metadata['id']}: {e}")
                    continue
            
            return archivos
            
        except Exception as e:
            print(f"⚠️ Error obteniendo archivos: {e}")
            return []
        finally:
            conn.close()

    def obtener_archivos_por_contrato(self, contrato_id):
        """
        OBTENER TODOS LOS ARCHIVOS DE UN CONTRATO
        """
        try:
            archivos_totales = []
            
            archivos_categoria = self.obtener_archivos(contrato_id)
            archivos_totales.extend(archivos_categoria)
            
            return archivos_totales
            
        except Exception as e:
            print(f"⚠️ Error en obtener_archivos_por_contrato: {e}")
            return []

    def obtener_archivos_por_contrato_completo(self, contrato_id):
        """
        Obtener TODOS los archivos de un contrato, incluyendo el principal
        """
        try:
            archivos_totales = []
            
            # 1. Obtener el contrato principal
            contrato_principal = self.obtener_contrato_por_id(contrato_id)
            if contrato_principal:
                archivos_totales.append({
                    'id': f"principal_{contrato_id}",
                    'contrato_id': contrato_id,
                    'categoria': 'CONTRATO',
                    'nombre_archivo': contrato_principal['metadata'].get('nombre_archivo', 'contrato_principal.pdf'),
                    'tipo_archivo': contrato_principal['metadata'].get('tipo_archivo', 'application/pdf'),
                    'tamaño_bytes': contrato_principal['metadata'].get('tamaño_bytes', 0),
                    'contenido': contrato_principal['contenido'],
                    'es_principal': True
                })
            
            # 2. Obtener archivos adicionales
            archivos_adicionales = self.obtener_archivos(contrato_id)
            for archivo in archivos_adicionales:
                archivo['es_principal'] = False
                archivos_totales.append(archivo)
            
            return archivos_totales
            
        except Exception as e:
            print(f"⚠️ Error obteniendo archivos completos: {e}")
            return []

    def eliminar_archivo(self, archivo_id, categoria=None):
        """
        ELIMINAR ARCHIVO INDIVIDUAL
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            if categoria:
                cur.execute("SELECT lo_oid FROM archivos_pemex WHERE id = %s AND categoria = %s", 
                          (archivo_id, categoria))
            else:
                cur.execute("SELECT lo_oid FROM archivos_pemex WHERE id = %s", (archivo_id,))
            
            resultado = cur.fetchone()
            
            if resultado:
                lo_oid = resultado[0]
                
                if categoria:
                    cur.execute("DELETE FROM archivos_pemex WHERE id = %s AND categoria = %s", 
                              (archivo_id, categoria))
                else:
                    cur.execute("DELETE FROM archivos_pemex WHERE id = %s", (archivo_id,))
                
                try:
                    large_obj = conn.lobject(lo_oid)
                    large_obj.unlink()
                except:
                    pass
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error eliminando archivo: {str(e)}")
        finally:
            conn.close()

    def eliminar_archivos_contrato(self, contrato_id):
        """
        ELIMINAR TODOS LOS ARCHIVOS DE UN CONTRATO
        """
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            cur.execute("SELECT lo_oid FROM archivos_pemex WHERE contrato_id = %s", (contrato_id,))
            oids = cur.fetchall()
            
            cur.execute("DELETE FROM archivos_pemex WHERE contrato_id = %s", (contrato_id,))
            
            for (lo_oid,) in oids:
                try:
                    large_obj = conn.lobject(lo_oid)
                    large_obj.unlink()
                except:
                    pass
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"Error eliminando archivos del contrato: {str(e)}")
        finally:
            conn.close()

    # ============================================
    # FUNCIONES ADICIONALES PARA MEJOR FUNCIONALIDAD
    # ============================================

    def contar_archivos_por_contrato(self, contrato_id):
        """Contar cuántos archivos tiene un contrato"""
        conn = self._get_connection()
        try:
            self.verificar_tabla_archivos()
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT COUNT(*) as total
                FROM archivos_pemex
                WHERE contrato_id = %s
            """, (contrato_id,))
            
            resultado = cur.fetchone()
            return resultado[0] if resultado else 0
            
        except Exception as e:
            print(f"⚠️ Error contando archivos: {e}")
            return 0
        finally:
            conn.close()

    def obtener_categorias_archivos(self, contrato_id):
        """Obtener las categorías únicas de archivos que tiene un contrato"""
        conn = self._get_connection()
        try:
            self.verificar_tabla_archivos()
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT DISTINCT categoria
                FROM archivos_pemex
                WHERE contrato_id = %s
                ORDER BY categoria
            """, (contrato_id,))
            
            categorias = [row[0] for row in cur.fetchall()]
            return categorias
            
        except Exception as e:
            print(f"⚠️ Error obteniendo categorías: {e}")
            return []
        finally:
            conn.close()

    def obtener_estadisticas_archivos(self):
        """Obtener estadísticas de archivos"""
        conn = self._get_connection()
        try:
            self.verificar_tabla_archivos()
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    COUNT(*) as total_archivos,
                    COUNT(DISTINCT contrato_id) as contratos_con_archivos,
                    SUM(tamaño_bytes) as total_bytes,
                    categoria,
                    COUNT(*) as cantidad_por_categoria
                FROM archivos_pemex
                GROUP BY categoria
                ORDER BY cantidad_por_categoria DESC
            """)
            
            resultados = cur.fetchall()
            columnas = [desc[0] for desc in cur.description]
            
            stats = {
                'total_archivos': 0,
                'contratos_con_archivos': 0,
                'total_bytes': 0,
                'categorias': []
            }
            
            for fila in resultados:
                row_dict = dict(zip(columnas, fila))
                stats['total_archivos'] += row_dict['cantidad_por_categoria']
                stats['contratos_con_archivos'] = row_dict['contratos_con_archivos']
                stats['total_bytes'] = row_dict['total_bytes'] or 0
                stats['categorias'].append(row_dict)
            
            return stats
            
        except Exception as e:
            print(f"⚠️ Error obteniendo estadísticas de archivos: {e}")
            return None
        finally:
            conn.close()

    def validar_archivo(self, contrato_id, categoria, nombre_archivo):
        """
        Validar si un archivo ya existe para evitar duplicados
        """
        conn = self._get_connection()
        try:
            self.verificar_tabla_archivos()
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT COUNT(*) 
                FROM archivos_pemex 
                WHERE contrato_id = %s 
                AND categoria = %s 
                AND nombre_archivo = %s
            """, (contrato_id, categoria, nombre_archivo))
            
            existe = cur.fetchone()[0] > 0
            return existe
            
        except Exception as e:
            print(f"⚠️ Error validando archivo: {e}")
            return False
        finally:
            conn.close()

    def obtener_ultimos_archivos(self, limite=10):
        """Obtener los últimos archivos subidos"""
        conn = self._get_connection()
        try:
            self.verificar_tabla_archivos()
            
            cur = conn.cursor()
            
            cur.execute("""
                SELECT a.*, c.numero_contrato, c.contratista
                FROM archivos_pemex a
                LEFT JOIN contratos_pemex c ON a.contrato_id = c.id
                ORDER BY a.fecha_subida DESC
                LIMIT %s
            """, (limite,))
            
            resultados = cur.fetchall()
            columnas = [desc[0] for desc in cur.description]
            
            archivos = []
            for fila in resultados:
                archivos.append(dict(zip(columnas, fila)))
            
            return archivos
            
        except Exception as e:
            print(f"⚠️ Error obteniendo últimos archivos: {e}")
            return []
        finally:
            conn.close()

# Función para obtener el manager - MANTENIDA SIN CAMBIOS
@st.cache_resource
def get_db_manager():
    connection_string = "postgresql://pemex_contratos_user:j2OyFqPrwkAQelnX9TVSXFrlWsekAkdH@dpg-d4gaap3uibrs73998am0-a:5432/pemex_contratos"
    
    try:
        manager = ContratosManager(connection_string)
        if manager.init_db():
            st.success("✅ Conectado a PostgreSQL")
            return manager
        else:
            st.error("❌ No se pudo inicializar la base de datos")
            return None
    except Exception as e:
        st.error(f"❌ Error conectando a PostgreSQL: {str(e)}")
        return None