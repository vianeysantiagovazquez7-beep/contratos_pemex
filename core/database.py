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
            # SOLUCIÓN: Convertir bool a string numérico
            return "1" if value else "0"
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, (list, dict)):
            try:
                return json.dumps(value, ensure_ascii=False)
            except:
                return str(value)
        else:
            # Conversión absoluta
            return str(value)

    def _debug_datos(self, datos, titulo):
        """Debugging extensivo"""
        print(f"🔍 {titulo}:")
        for key, value in datos.items():
            print(f"  {key}: {repr(value)} (tipo: {type(value).__name__})")

    def guardar_contrato_pemex(self, archivo, datos_extraidos, usuario="sistema"):
        """
        Guardar contrato en PostgreSQL - VERSIÓN DEFINITIVA
        """
        conn = self._get_connection()
        try:
            # DEBUG EXTENSIVO
            self._debug_datos(datos_extraidos, "DEBUG DATOS CRUDOS")
            
            file_bytes = archivo.getvalue()
            file_hash = self.calcular_hash(file_bytes)
            
            # Crear Large Object
            lo_oid = conn.lobject(0, 'wb', 0, True)
            
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
            
            # ⚠️ SOLUCIÓN DEFINITIVA PARA PLAZO
            plazo_original = datos_extraidos.get('plazo', '')
            print(f"🚨 PLAZO ORIGINAL: {repr(plazo_original)} (tipo: {type(plazo_original).__name__})")
            
            plazo = self._safe_string(plazo_original)
            print(f"🚨 PLAZO CONVERTIDO: {repr(plazo)} (tipo: {type(plazo).__name__})")
            
            # VERIFICACIÓN FINAL
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
            # Debug antes de procesar
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
            # NO HAY RESPALDO LOCAL - solo PostgreSQL
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

# Función para obtener el manager
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
    