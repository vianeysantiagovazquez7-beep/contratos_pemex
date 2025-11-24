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
            
            # Guardar TODOS los metadatos PEMEX
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
                datos_extraidos.get('contrato', ''),
                datos_extraidos.get('contratista', ''),
                datos_extraidos.get('monto', ''),
                datos_extraidos.get('plazo', ''),
                datos_extraidos.get('objeto', ''),
                json.dumps(datos_extraidos.get('anexos', [])),  # Guardar anexos como JSON
                lo_oid.oid,
                archivo.name,
                getattr(archivo, 'type', 'application/pdf'),
                len(file_bytes),
                file_hash,
                usuario
            ))
            
            contrato_id = cur.fetchone()[0]
            conn.commit()
            return contrato_id
            
        except psycopg2.IntegrityError:
            conn.rollback()
            raise Exception("❌ Ya existe un contrato con ese número")
        except Exception as e:
            conn.rollback()
            raise Exception(f"❌ Error guardando contrato: {str(e)}")
        finally:
            conn.close()
    
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