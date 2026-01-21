# Resumen de Proyectos OCR

## 1. ocr/
**Descripcion:** Scripts Python para conversion de PDF a DOCX de documentos dentales.

**Tecnologias:**
- Tesseract OCR
- OpenCV + scikit-image (preprocesamiento)
- PyMuPDF, pdf2image
- python-docx

**Caracteristicas:**
- Multiples versiones del conversor (v3.4 es la mas reciente)
- Deteccion de filas usando lineas horizontales
- Deskewing con rotacion fija
- Extraccion basada en plantillas conocidas
- Inferencia de numeros de catalogo secuenciales (AI-DI-XX-YYY)
- Remocion de lineas antes de OCR

**Archivos principales:**
- `convert_dental_v3.4.py` - Version principal
- `convert_final.py`, `convert_skimage_fixed.py`

---

## 2. ocr-ana/
**Descripcion:** Conversor simple PDF a DOCX usando Google Cloud Vision.

**Tecnologias:**
- Google Cloud Vision API
- python-docx
- pdf2image

**Caracteristicas:**
- OCR basico con Vision API
- Extraccion de tablas por patrones de texto
- Deteccion de numeros de catalogo con regex
- Generacion de DOCX formateado

**Archivos principales:**
- `pdf_to_docx.py`
- Documentos de prueba: `INSTRUMENTOS DENTALES.pdf/docx`

---

## 3. ocr-ana-v2/
**Descripcion:** Pipeline OCR completo con Google Document AI.

**Tecnologias:**
- Google Document AI (OCR avanzado)
- Google Cloud Vision (alternativa)
- Google Cloud Storage
- PyMuPDF, OpenCV, NumPy, scikit-image
- python-docx

**Pipeline de 5 fases:**
1. **Preprocesamiento local** - PyMuPDF extrae imagenes, OpenCV aplica grayscale/deskew/denoise
2. **Cloud Storage** - Almacenamiento temporal para batch
3. **Document AI** - OCR + deteccion de layout/tablas/formularios
4. **Post-procesamiento** - Ordenar bloques, clasificar elementos, reconstruir tablas
5. **Generacion DOCX** - Headings, paragraphs, tables con estilos

**Caracteristicas:**
- Deteccion de layout avanzada
- Deteccion nativa de tablas
- Coordenadas precisas (bounding boxes)
- Estructura jerarquica: Pagina -> Bloque -> Parrafo -> Linea -> Token

**Archivos principales:**
- `ocr_pipeline.py`, `ocr_pipeline_v2.py`, `ocr_pipeline_v3.py`, `ocr_pipeline_v4.py`
- `ARQUITECTURA.md` - Documentacion completa del pipeline

---

## 4. ocr-v2/
**Descripcion:** Motor OCR de produccion con deteccion inteligente de tipo de PDF.

**Tecnologias:**
- PyMuPDF
- Tesseract OCR
- OpenCV
- scikit-learn (ML simple)
- python-docx, ReportLab

**Caracteristicas:**
- **Deteccion de tipo de PDF:** SCANNED, TEXT-based, MIXED
- **Preprocesamiento adaptativo:** Deskew, denoise, contraste, binarizacion
- **Deteccion de tablas:** Lineas morfologicas
- **Multiples formatos de salida:** DOCX, TXT, JSON, Searchable PDF, hOCR
- **Procesamiento batch** con ejecucion paralela
- **Soporte Docker**
- **Presets configurables:** default, high_quality, fast

**Estructura del proyecto:**
```
src/ocr_engine/
├── cli.py, config.py, pipeline.py
├── models/, detection/, preprocessing/
├── layout/, ocr/, output/, ml/
```

**Archivos principales:**
- `README.md` - Documentacion completa
- `src/` - Codigo fuente modular

---

## 5. projects/
**Descripcion:** Motor OCR v2.1 - Version mas avanzada y completa.

**Tecnologias:**
- PyMuPDF
- Tesseract OCR
- NumPy, OpenCV
- python-docx
- Typer (CLI)

**Caracteristicas avanzadas:**
- **TransformChain:** Precision sub-pixel en todas las transformaciones
- **Modos de PDF:** TEXT (vector), SCANNED (raster), MIXED
- **Trusted masking:** Evita texto duplicado en PDFs mixtos
- **Reading Order:** Algoritmo XY-Cut para ordenamiento multi-columna
- **Header/Footer Detection:** Identificacion automatica
- **Reparacion de texto:** Heuristicas para palabras divididas
- **Image Fallback:** Regiones de baja confianza se convierten a imagenes

**8 fases implementadas:**
1. Scaffolding + configuracion
2. Geometria + TransformChain
3. Modelos IR + writers (JSON)
4. PDF ingest + extraccion vectorial
5. Raster rendering + preprocesamiento
6. OCR + postprocess
7. Mixed-mode handling
8. Validacion, writers, regression gates

**Formatos de salida:**
- JSON IR (representacion intermedia)
- DOCX
- Plain text
- hOCR
- Searchable PDF

**Testing:** 64 tests (21 unit + 43 integration)

**Estructura del proyecto:**
```
src/ocr_engine/
├── cli.py, config.py, pipeline.py
├── geometry/ (spaces, bboxes, transforms)
├── ir/ (models, ordering, provenance)
├── ingest/, extraction/, preprocessing/
├── detection/, ocr/, validation/, output/, layout/
```

**Archivos principales:**
- `README.md`, `ARCHITECTURE.md`, `PLAN.md`
- `OPTIMIZATION.md`, `TODO.md`

---

## Comparativa

| Proyecto | Complejidad | OCR Engine | Cloud | Produccion |
|----------|-------------|------------|-------|------------|
| ocr | Media | Tesseract | No | No |
| ocr-ana | Baja | Google Vision | Si | No |
| ocr-ana-v2 | Media-Alta | Document AI | Si | No |
| ocr-v2 | Alta | Tesseract | No | Si |
| projects | Muy Alta | Tesseract | No | Si |

---

## Recomendaciones

1. **Para uso simple:** `ocr-ana` o `ocr` para documentos especificos
2. **Para mejor OCR:** `ocr-ana-v2` con Google Document AI
3. **Para produccion local:** `projects` (ocr-v2.1) - el mas completo y robusto
4. **Para Docker/batch:** `ocr-v2`

---

*Generado: 2026-01-20*
