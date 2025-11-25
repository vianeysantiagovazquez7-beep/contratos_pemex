# core/database.py
import psycopg2
import psycopg2.extensions
from psycopg2 import sql
import hashlib
from datetime import datetime
import io
import streamlit as st
import json
import os  
import uuid
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
            
            # Tabla completa con todos tus campos específicos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS contratos_pemex (
                    id BIGSERIAL PRIMARY KEY,
                    -- Campos específicos PEMEX
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
            
            # Índices para búsquedas rápidas PEMEX
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contratos_numero ON contratos_pemex(numero_contrato)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contratos_contratista ON contratos_pemex(contratista)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contratos_area ON contratos_pemex(area)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_contratos_fecha ON contratos_pemex(fecha_subida)")
            
            conn.commit()
            st.success("✅ Base de datos PEMEX inicializada")
            return True
            
        except Exception as e:
            conn.rollback()
            st.error(f"❌ Error inicializando BD: {str(e)}")
            return False
        finally:
            conn.close()
    
    def calcular_hash(self, file_bytes):
        return hashlib.sha256(file_bytes).hexdigest()

    def _safe_string(self, value):
        """Convierte cualquier valor a string de forma 100% segura"""
        if value is None:
            return ""
        elif isinstance(value, bool):
            return "True" if value else "False"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, dict)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except:
                return str(value)
        else:
            return str(value)
    
    def _guardar_localmente(self, archivos_data, datos_contrato):
        """Guardar contrato localmente como respaldo"""
        # Crear directorio de respaldo si no existe
        backup_dir = "backup_contratos"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Generar nombre único
        backup_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"contrato_backup_{timestamp}_{backup_id}.json"
        filepath = os.path.join(backup_dir, filename)
        
        # Preparar datos para backup (convertir a tipos serializables)
        backup_data = {
            'metadata': {},
            'timestamp': timestamp,
            'backup_id': backup_id,
            'archivos': {
                'principal': archivos_data['principal'].name if archivos_data.get('principal') else None,
                'anexos_count': len(archivos_data.get('anexos', [])),
                'cedulas_count': len(archivos_data.get('cedulas', [])),
                'soportes_count': len(archivos_data.get('soportes', []))
            }
        }
        
        # Convertir todos los valores a string para el backup
        for key, value in datos_contrato.items():
            backup_data['metadata'][key] = self._safe_string(value)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        return filepath

    def guardar_contrato_pemex(self, archivo, datos_extraidos, usuario="sistema"):
        """
        Guardar contrato con TODOS los datos PEMEX extraídos
        """
        conn = self._get_connection()
        try:
            file_bytes = archivo.getvalue()
            file_hash = self.calcular_hash(file_bytes)
            
            # Crear Large Object (hasta 4TB)
            lo_oid = conn.lobject(0, 'wb', 0, True)
            
            # Escribir archivo en chunks
            chunk_size = 1024 * 1024
            with io.BytesIO(file_bytes) as file_stream:
                while True:
                    chunk = file_stream.read(chunk_size)
                    if not chunk:
                        break
                    lo_oid.write(chunk)
            
            # CONVERSIÓN 100% SEGURA DE TODOS LOS CAMPOS
            contrato = self._safe_string(datos_extraidos.get('contrato', ''))
            contratista = self._safe_string(datos_extraidos.get('contratista', ''))
            monto = self._safe_string(datos_extraidos.get('monto', ''))
            plazo = self._safe_string(datos_extraidos.get('plazo', ''))
            objeto = self._safe_string(datos_extraidos.get('objeto', ''))
            anexos = json.dumps(datos_extraidos.get('anexos', []), ensure_ascii=False)
            
            # DEBUG DETALLADO: Mostrar en logs de Render
            print("🔍 DEBUG DETALLADO - Valores a insertar en PostgreSQL:")
            print(f"  contrato: {repr(contrato)} (tipo: {type(contrato).__name__})")
            print(f"  contratista: {repr(contratista)} (tipo: {type(contratista).__name__})")
            print(f"  monto: {repr(monto)} (tipo: {type(monto).__name__})")
            print(f"  plazo: {repr(plazo)} (tipo: {type(plazo).__name__})")
            print(f"  objeto: {repr(objeto)} (tipo: {type(objeto).__name__})")
            
            # VERIFICACIÓN FINAL DE SEGURIDAD - asegurar que plazo es string
            if not isinstance(plazo, str):
                print(f"🚨 ¡CRÍTICO! plazo NO es string: {repr(plazo)} (tipo: {type(plazo).__name__})")
                # Forzar conversión
                plazo = str(plazo)
                print(f"🚨 plazo convertido forzadamente: {repr(plazo)} (tipo: {type(plazo).__name__})")
            
            # Guardar en PostgreSQL
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
                contrato,
                contratista,
                monto,
                plazo,  # ¡Ahora 100% garantizado que es string!
                objeto,
                anexos,
                lo_oid.oid,
                archivo.name,
                getattr(archivo, 'type', 'application/pdf'),
                len(file_bytes),
                file_hash,
                usuario
            ))
            
            contrato_id = cur.fetchone()[0]
            conn.commit()
            
            print(f"✅ CONTRATO GUARDADO EXITOSAMENTE EN POSTGRESQL - ID: {contrato_id}")
            return contrato_id
            
        except psycopg2.IntegrityError:
            conn.rollback()
            raise Exception("❌ Ya existe un contrato con ese número")
        except Exception as e:
            conn.rollback()
            print(f"🔴 ERROR DETALLADO en guardar_contrato_pemex:")
            print(f"   Tipo de error: {type(e).__name__}")
            print(f"   Mensaje: {str(e)}")
            print(f"   Traceback: {traceback.format_exc()}")
            raise Exception(f"❌ Error guardando contrato: {str(e)}")
        finally:
            conn.close()

    def guardar_contrato_completo(self, archivos_data, datos_contrato, usuario="sistema"):
        """
        Guardar contrato completo con todos los archivos (principal, anexos, cédulas, soportes)
        """
        try:
            # DEBUG DETALLADO ANTES de cualquier procesamiento
            print("🔍 DEBUG - VALORES ORIGINALES DE datos_contrato:")
            for key, value in datos_contrato.items():
                print(f"  {key}: {repr(value)} (tipo: {type(value).__name__})")
            
            # VERIFICACIÓN EXTRA: Asegurar que todos los campos sean strings
            datos_limpios = {}
            for key, value in datos_contrato.items():
                valor_original = value
                valor_convertido = self._safe_string(value)
                datos_limpios[key] = valor_convertido
                
                # Debug específico para plazo
                if key == 'plazo':
                    print(f"🚨 DEBUG ESPECÍFICO PLAZO:")
                    print(f"   Valor original: {repr(valor_original)}")
                    print(f"   Tipo original: {type(valor_original).__name__}")
                    print(f"   Valor convertido: {repr(valor_convertido)}")
                    print(f"   Tipo convertido: {type(valor_convertido).__name__}")
            
            # Debug final de datos limpios
            print("🔍 DEBUG - VALORES LIMPIOS (después de _safe_string):")
            for key, value in datos_limpios.items():
                print(f"  {key}: {repr(value)} (tipo: {type(value).__name__})")
            
            # Usar el archivo principal para guardar en la base de datos
            archivo_principal = archivos_data['principal']
            
            # Guardar usando el método existente
            contrato_id = self.guardar_contrato_pemex(archivo_principal, datos_limpios, usuario)
            
            if contrato_id:
                st.success(f"🗄️ **Contrato guardado en PostgreSQL** (ID: {contrato_id})")
                
                # Log opcional de archivos adicionales
                anexos_count = len(archivos_data.get('anexos', []))
                cedulas_count = len(archivos_data.get('cedulas', []))
                soportes_count = len(archivos_data.get('soportes', []))
                
                if anexos_count > 0:
                    st.info(f"📎 {anexos_count} anexos registrados")
                if cedulas_count > 0:
                    st.info(f"📊 {cedulas_count} cédulas asociadas")
                if soportes_count > 0:
                    st.info(f"📄 {soportes_count} soportes incluidos")
            
            return contrato_id
            
        except Exception as e:
            st.error(f"❌ Error guardando en PostgreSQL: {str(e)}")
            
            # Debug adicional del error
            error_details = traceback.format_exc()
            print(f"🔴 ERROR COMPLETO en guardar_contrato_completo:")
            print(error_details)
            
            # Guardar localmente como respaldo
            try:
                backup_path = self._guardar_localmente(archivos_data, datos_contrato)
                st.info(f"📁 El contrato se guardó localmente en: {backup_path}")
                st.warning("⚠️ El contrato se guardó localmente, pero hubo problemas con PostgreSQL")
            except Exception as backup_error:
                st.error(f"🔴 Error incluso guardando localmente: {backup_error}")
            
            raise Exception(f"Error guardando contrato completo: {str(e)}")
    
    def buscar_contratos_pemex(self, filtros=None):
        """Búsqueda avanzada para PEMEX"""
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
                
                if 'descripcion' in filtros and filtros['descripcion']:
                    where_conditions.append("descripcion ILIKE %s")
                    params.append(f"%{filtros['descripcion']}%")
                
                if 'area' in filtros and filtros['area']:
                    where_conditions.append("area ILIKE %s")
                    params.append(f"%{filtros['area']}%")
            
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
                else:
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
            
            # Recuperar Large Object
            lo_oid = metadata['lo_oid']
            large_obj = conn.lobject(lo_oid, 'rb')
            
            chunks = []
            chunk_size = 1024 * 1024
            while True:
                chunk = large_obj.read(chunk_size)
                if not chunk:
                    break
                chunks.append(chunk)
            
            contenido = b''.join(chunks)
            
            # Verificar integridad
            hash_calculado = self.calcular_hash(contenido)
            if hash_calculado != metadata['hash_sha256']:
                st.warning("⚠️ Advertencia: El hash del archivo no coincide")
            
            return {
                'metadata': metadata,
                'contenido': contenido
            }
            
        except Exception as e:
            raise Exception(f"❌ Error obteniendo contrato: {str(e)}")
        finally:
            conn.close()
    
    def eliminar_contrato(self, contrato_id):
        """Eliminar contrato de la base de datos"""
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
                    pass  # El objeto podría ya estar eliminado
            
            conn.commit()
            return True
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"❌ Error eliminando contrato: {str(e)}")
        finally:
            conn.close()
    
    def obtener_estadisticas_pemex(self):
        """Obtener estadísticas específicas para PEMEX"""
        conn = self._get_connection()
        try:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    COUNT(*) as total_contratos,
                    COALESCE(SUM(tamaño_bytes), 0) as total_bytes,
                    COUNT(DISTINCT contratista) as contratistas_unicos,
                    COUNT(DISTINCT area) as areas_activas,
                    MIN(fecha_subida) as fecha_mas_antigua,
                    MAX(fecha_subida) as fecha_mas_reciente
                FROM contratos_pemex
            """)
            
            stats = dict(zip(['total_contratos', 'total_bytes', 'contratistas_unicos', 
                            'areas_activas', 'fecha_mas_antigua', 'fecha_mas_reciente'], 
                           cur.fetchone()))
            
            # Formatear fechas
            if stats['fecha_mas_antigua']:
                stats['fecha_mas_antigua'] = stats['fecha_mas_antigua'].strftime('%Y-%m-%d')
            if stats['fecha_mas_reciente']:
                stats['fecha_mas_reciente'] = stats['fecha_mas_reciente'].strftime('%Y-%m-%d')
            
            return stats
            
        except Exception as e:
            raise Exception(f"❌ Error obteniendo estadísticas: {str(e)}")
        finally:
            conn.close()

# Función para obtener el manager - VERSIÓN SIMPLIFICADA
@st.cache_resource
def get_db_manager():
    # VALOR DIRECTO - sin depender de variables de entorno
    connection_string = "postgresql://pemex_contratos_user:j2OyFqPrwkAQelnX9TVSXFrlWsekAkdH@dpg-d4gaap3uibrs73998am0-a:5432/pemex_contratos"
    
    try:
        manager = ContratosManager(connection_string)
        if manager.init_db():
            st.success("✅ Conectado a PostgreSQL en Render")
            return manager
        else:
            st.warning("⚠️ No se pudo inicializar la base de datos")
            return None
    except Exception as e:
        st.warning(f"⚠️ Error conectando a PostgreSQL: {str(e)}")
        return None
    