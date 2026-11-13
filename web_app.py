# web_app.py
import os
import asyncio
import csv
from pathlib import Path
from flask import Flask, request, render_template_string, send_file, jsonify
from werkzeug.utils import secure_filename

from app import generate_full_package

app = Flask(__name__)

TEMP_DIR = Path(__file__).parent / "temp_files"
TEMP_DIR.mkdir(exist_ok=True)

HTML_TEMPLATE = """
<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>CardGen AI - Генератор описаний</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        :root {
            --bg-page: #0b0c10;
            --card-bg: #1a1c23;
            --primary-gradient: linear-gradient(135deg, #a855f7, #3b82f6);
            --text-white: #ffffff;
            --text-gray: #a0a0b0;
            --border: #2e303a;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: "Inter", system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
            background: var(--bg-page);
            color: var(--text-white);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        /* Шапка */
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem 2rem;
            border-bottom: 1px solid var(--border);
            background: #12141a;
        }
        .header-left { display: flex; align-items: center; gap: 1rem; }
        .logo { font-size: 20px; font-weight: 700; }
        .tabs { display: flex; gap: 1rem; }
        .tab { padding: 0.5rem 1rem; border-radius: 8px; cursor: pointer; color: var(--text-gray); }
        .tab.active { background: #2e303a; color: var(--text-white); }
        .profile { display: flex; align-items: center; gap: 0.5rem; }
        .avatar { width: 32px; height: 32px; border-radius: 50%; background: #7c3aed; display: flex; align-items: center; justify-content: center; font-size: 14px; }

        /* Основной контент */
        .main {
            flex: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
            width: 100%;
        }
        .page-title { font-size: 32px; font-weight: 700; margin-bottom: 0.5rem; }
        .page-subtitle { font-size: 14px; color: var(--text-gray); margin-bottom: 2rem; }

        .layout { display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; }
        .card { background: var(--card-bg); border-radius: 16px; padding: 1.5rem; border: 1px solid var(--border); }

        .form-group { margin-bottom: 1.5rem; }
        label { display: block; font-size: 14px; color: var(--text-gray); margin-bottom: 0.5rem; }
        textarea.input-field {
            width: 100%; padding: 1rem; background: #1e2029; 
            border: 1px solid var(--border); border-radius: 12px; 
            font-family: inherit; font-size: 14px; color: var(--text-white); 
            min-height: 120px; resize: vertical; transition: border-color 0.2s;
        }
        textarea.input-field:focus { outline: none; border-color: #7c3aed; }
        .btn {
            display: inline-flex; align-items: center; gap: 0.5rem; 
            padding: 0.875rem 1.5rem; background: var(--primary-gradient); color: white; 
            border: none; border-radius: 12px; font-family: inherit; font-size: 14px; 
            font-weight: 500; cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; 
            margin-top: 0.5rem; width: 100%; justify-content: center;
        }
        .btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(124,58,237,0.3); }
        .btn:active { transform: translateY(0); }

        .file-upload {
            border: 2px dashed var(--border); border-radius: 12px; padding: 2rem; 
            text-align: center; transition: border-color 0.2s, background 0.2s; cursor: pointer;
        }
        .file-upload:hover { border-color: #7c3aed; }
        .file-upload.drag-over { border-color: #7c3aed; background: rgba(124,58,237,0.05); }
        .upload-icon { width: 32px; height: 32px; margin: 0 auto 0.75rem; stroke: var(--text-gray); }
        .upload-text { color: var(--text-white); font-size: 14px; margin-top: 0.25rem; display: block; font-weight: 500; }
        .upload-hint { font-size: 12px; color: #6b7280; margin-top: 0.5rem; display: block; }
        .choose-btn {
            display: inline-flex; align-items: center; gap: 0.5rem;
            margin-top: 1rem; padding: 0.5rem 1rem; background: #2e303a;
            color: var(--text-white); border: 1px solid var(--border); border-radius: 8px;
            font-size: 13px; cursor: pointer;
        }
        .choose-btn:hover { background: #3e4050; }

        .preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .preview-title { font-size: 14px; color: var(--text-gray); display: flex; align-items: center; gap: 0.5rem; }
        .ready-badge { font-size: 11px; background: #2e303a; color: var(--text-gray); padding: 0.25rem 0.5rem; border-radius: 4px; }

        .preview-card { background: #1e2029; border-radius: 12px; padding: 1.5rem; height: 100%; }
        .preview-stripes {
            height: 20px; background: repeating-linear-gradient(45deg,#2e303a,#2e303a 4px,#23252d 4px,#23252d 8px); 
            border-radius: 4px; margin-bottom: 1rem;
        }
        .preview-image {
            width: 60px; height: 60px; background: #2e303a; border-radius: 6px; 
            margin: 1rem 0; display: flex; align-items: center; justify-content: center; 
            color: #6b7280;
        }
        .preview-line { height: 8px; background: #2e303a; border-radius: 4px; margin: 0.75rem 0; }
        .preview-line.short { width: 60%; }
        .rating { display: flex; gap: 2px; margin-top: 1rem; }
        .rating-star { width: 12px; height: 12px; background: #fbbf24; border-radius: 2px; }
        .rating-star.empty { background: #2e303a; }
        .copy-btn-small {
            background: #2e303a; color: var(--text-white); border: none; padding: 0.5rem 1rem; 
            border-radius: 4px; font-size: 12px; margin-top: 1rem; cursor: pointer; display: flex; align-items: center; gap: 0.5rem;
        }
        .copy-btn-small:hover { background: #3e4050; }

        #progress { display: none; margin: 1rem 0; color: var(--text-gray); }
        #error { display: none; color: #f87171; margin: 1rem 0; }
        #result { display: none; margin: 1rem 0; white-space: pre-wrap; font-size: 14px; }
        #downloads { margin-top: 1rem; }
        .download-btn { 
            display: inline-block; margin-right: 1rem; margin-top: 0.5rem; padding: 0.5rem 1rem; 
            background: #10b981; color: white; text-decoration: none; border-radius: 6px; font-size: 14px;
        }
        .download-btn:hover { background: #059669; }
        @media (max-width: 768px) {
            .layout { grid-template-columns: 1fr; }
            .header { flex-direction: column; gap: 1rem; }
        }
    </style>
</head>
<body>
    <!-- Шапка -->
    <div class="header">
        <div class="header-left">
            <div class="logo">CardGen AI</div>
        </div>
        <div class="tabs">
            <div class="tab active">Один товар</div>
            <div class="tab">Пакетная обработка</div>
        </div>
        <div class="profile">
            <div class="avatar">А</div>
            <div>Алексей</div>
        </div>
    </div>

    <!-- Основной контент -->
    <div class="main">
        <h1 class="page-title">Генератор описаний для WB и Ozon.</h1>
        <p class="page-subtitle">Создавайте продающие описания товаров для Wildberries и Ozon за секунды с помощью AI.</p>

        <div class="layout">
            <!-- Левая колонка -->
            <div class="card">
                <div class="form-group">
                    <label for="product">Название товара ✨</label>
                    <textarea id="product" class="input-field" placeholder="Введите название товара, для которого нужно сгенерировать описание..."></textarea>
                    <button type="button" class="btn" onclick="generateSingle()">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>Сгенерировать описание
                    </button>
                </div>

                <div class="form-group">
                    <label>Загрузить файл:</label>
                    <div class="file-upload" id="fileUpload" ondragover="handleDragOver(event)" ondragleave="handleDragLeave(event)" onclick="document.getElementById('fileInput').click()">
                        <svg class="upload-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><path d="M8 12h8M12 8v8"/></svg>
                        <span class="upload-text" id="uploadText">Перетащите .xlsx / .csv</span>
                        <span class="upload-hint" id="uploadHint">или выберите файл с товарами</span>
                        <div class="choose-btn">📁 Выбрать файл</div>
                    </div>
                    <input type="file" id="fileInput" accept=".xlsx,.csv" style="display:none"/>
                    <button type="button" class="btn" onclick="generateFile()" style="margin-top: 1rem;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg>Обработать файл
                    </button>
                </div>

                <div id="progress" class="progress">Обработка...</div>
                <div id="error" class="error"></div>
                <div id="result" class="description"></div>
                <div id="downloads"></div>
            </div>

            <!-- Правая колонка (предпросмотр) -->
            <div class="card">
                <div class="preview-header">
                    <div class="preview-title">👁 Предпросмотр карточки</div>
                    <div class="ready-badge">Готово к копированию</div>
                </div>
                <div class="preview-card" id="previewCard">
                    <div class="preview-stripes"></div>
                    <div class="preview-line short"></div>
                    <div class="preview-line"></div>
                    <div class="preview-image">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                    </div>
                    <div class="preview-line"></div>
                    <div class="preview-line short"></div>
                    <div class="rating">
                        <div class="rating-star"></div>
                        <div class="rating-star"></div>
                        <div class="rating-star"></div>
                        <div class="rating-star"></div>
                        <div class="rating-star"></div>
                        <div class="rating-star empty"></div>
                    </div>
                    <button class="copy-btn-small" onclick="copyPreview()">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>Копировать
                    </button>
                </div>
            </div>
        </div>
    </div>

    <script>
        function showElement(id, show) {
            document.getElementById(id).style.display = show ? 'block' : 'none';
        }
        function handleDragOver(e) {
            e.preventDefault();
            document.getElementById('fileUpload').classList.add('drag-over');
        }
        function handleDragLeave(e) {
            document.getElementById('fileUpload').classList.remove('drag-over');
        }
        document.getElementById('fileInput').addEventListener('change', function(e) {
            const fileName = e.target.files[0] ? e.target.files[0].name : 'Файл не выбран';
            document.getElementById('uploadText').textContent = fileName;
            document.getElementById('uploadHint').textContent = 'Файл выбран. Нажмите "Обработать файл"';
        });

        async function generateSingle() {
            const product = document.getElementById('product').value.trim();
            if (!product) { alert('Введите название товара'); return; }
            showElement('progress', true); showElement('error', false); showElement('result', false);
            document.getElementById('downloads').innerHTML = '';
            try {
                const resp = await fetch('/generate_single', {
                    method: 'POST', headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({product_name: product})
                });
                const data = await resp.json();
                showElement('progress', false);
                if (data.error) {
                    showElement('error', true);
                    document.getElementById('error').textContent = '❌ ' + data.error;
                } else {
                    showElement('result', true);
                    document.getElementById('result').textContent = data.description;
                    document.getElementById('downloads').innerHTML =
                        `<a href="/download_file?file=${encodeURIComponent(data.pdf_file)}" class="download-btn">📄 Скачать PDF</a>` +
                        `<a href="/download_file?file=${encodeURIComponent(data.xlsx_file)}" class="download-btn">📊 Скачать Excel</a>`;
                }
            } catch (e) {
                showElement('progress', false); showElement('error', true);
                document.getElementById('error').textContent = '❌ Ошибка сети: ' + e.message;
            }
        }
        async function generateFile() {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files.length) { alert('Выберите файл'); return; }
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('file', file);
            showElement('progress', true); showElement('error', false); showElement('result', false);
            document.getElementById('downloads').innerHTML = '';
            try {
                const resp = await fetch('/generate_file', { method: 'POST', body: formData });
                const data = await resp.json();
                showElement('progress', false);
                if (data.error) {
                    showElement('error', true);
                    document.getElementById('error').textContent = '❌ ' + data.error;
                } else {
                    showElement('result', true);
                    document.getElementById('result').textContent = data.message;
                    document.getElementById('downloads').innerHTML =
                        `<a href="/download_file?file=${encodeURIComponent(data.xlsx_file)}" class="download-btn">📊 Скачать Excel</a>` +
                        `<a href="/download_file?file=${encodeURIComponent(data.pdf_file)}" class="download-btn">📄 Скачать PDF</a>`;
                }
            } catch (e) {
                showElement('progress', false); showElement('error', true);
                document.getElementById('error').textContent = '❌ Ошибка сети: ' + e.message;
            }
        }
        function copyPreview() {
            const preview = document.getElementById('previewCard').innerText;
            navigator.clipboard.writeText(preview).then(() => { alert('Текст скопирован!'); });
        }
    </script>
</body>
</html>
"""

def create_xlsx_file(results: list, user_id: int = 0) -> str:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    wb = Workbook()
    ws = wb.active
    ws.title = "Карточки товаров"
    headers = ["Товар", "Заголовок", "Описание", "Ключевые слова", "Хэштеги"]
    ws.append(headers)
    header_font = Font(name='Arial', size=12, bold=True, color='FFFFFF')
    data_font = Font(name='Arial', size=11, color='000000')
    header_fill = PatternFill(start_color='1F4E78', end_color='1F4E78', fill_type='solid')
    data_fill = PatternFill(start_color='F2F2F2', end_color='F2F2F2', fill_type='solid')
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
    ws.column_dimensions["A"].width = 25
    ws.column_dimensions["B"].width = 35
    ws.column_dimensions["C"].width = 40
    ws.column_dimensions["D"].width = 25
    ws.column_dimensions["E"].width = 20
    for i, result in enumerate(results, 2):
        ws.cell(row=i, column=1, value=result.get("product", ""))
        ws.cell(row=i, column=2, value=result.get("heading", ""))
        ws.cell(row=i, column=3, value=result.get("description", ""))
        ws.cell(row=i, column=4, value=result.get("keywords", ""))
        ws.cell(row=i, column=5, value=result.get("hashtags", ""))
        for cell in ws[i]:
            cell.font = data_font
            cell.fill = data_fill
            cell.border = thin_border
            cell.alignment = Alignment(vertical='top', wrap_text=True)
    xlsx_path = str(TEMP_DIR / f"products_{user_id}.xlsx")
    wb.save(xlsx_path)
    return xlsx_path

def create_pdf_file(results: list, user_id: int = 0) -> str:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_LEFT
    pdf_path = str(TEMP_DIR / f"products_{user_id}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    try:
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        font_name = 'DejaVuSans'
    except:
        font_name = 'Helvetica'
    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('Normal', fontName=font_name, fontSize=10, leading=14, alignment=TA_LEFT)
    style_bold = ParagraphStyle('Bold', fontName=font_name, fontSize=12, leading=16, spaceAfter=6)
    style_title = ParagraphStyle('Title', fontName=font_name, fontSize=16, leading=20, spaceAfter=12, alignment=1)
    elements = []
    for idx, res in enumerate(results):
        if idx > 0:
            elements.append(PageBreak())
        elements.append(Paragraph(f"<b>Товар:</b> {res.get('product', '')}", style_title))
        elements.append(Paragraph(f"<b>Заголовок:</b> {res.get('heading', '')}", style_bold))
        elements.append(Paragraph(f"<b>Описание:</b> {res.get('description', '')}", style_normal))
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(f"<b>Ключевые слова:</b> {res.get('keywords', '')}", style_normal))
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph(f"<b>Хэштеги:</b> {res.get('hashtags', '')}", style_normal))
        elements.append(Spacer(1, 50*mm))
    doc.build(elements)
    return pdf_path

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/generate_single", methods=["POST"])
def generate_single():
    data = request.get_json()
    product_name = data.get("product_name", "").strip()
    if not product_name:
        return jsonify({"error": "Не указано название товара"}), 400
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(generate_full_package(product_name))
        loop.close()
        if not isinstance(result, dict) or result.get("error"):
            return jsonify({"error": "Не удалось сгенерировать описание"}), 500
        item = {
            "product": product_name,
            "heading": result.get("header", "")[:50],
            "description": result.get("description", ""),
            "keywords": result.get("keywords", ""),
            "hashtags": result.get("hashtags", "")
        }
        xlsx_path = create_xlsx_file([item], 0)
        pdf_path = create_pdf_file([item], 0)
        description = (
            f"--- Заголовок ({len(item['heading'])} символов) ---\n{item['heading']}\n\n"
            f"--- Описание (продающее) ---\n{item['description']}\n\n"
            f"--- Ключевые слова ---\n{item['keywords']}\n\n"
            f"--- Хэштеги ---\n{item['hashtags']}"
        )
        return jsonify({
            "description": description,
            "xlsx_file": os.path.basename(xlsx_path),
            "pdf_file": os.path.basename(pdf_path)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/generate_file", methods=["POST"])
def generate_file():
    if "file" not in request.files:
        return jsonify({"error": "Файл не загружен"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Пустое имя файла"}), 400
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["xlsx", "csv"]:
        return jsonify({"error": "Неподдерживаемый формат. Используйте .xlsx или .csv"}), 400

    file_path = str(TEMP_DIR / f"upload_{secure_filename(file.filename)}")
    file.save(file_path)

    products = []
    try:
        if ext == "xlsx":
            from openpyxl import load_workbook
            wb = load_workbook(file_path, read_only=True)
            ws = wb.active
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row[0] is not None:
                    products.append(str(row[0]).strip())
            wb.close()
        elif ext == "csv":
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)
                for row in reader:
                    if row and row[0] is not None:
                        products.append(str(row[0]).strip())
    except Exception as e:
        os.remove(file_path)
        return jsonify({"error": f"Ошибка чтения файла: {e}"}), 500
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if not products:
        return jsonify({"error": "В файле не найдено товаров"}), 400

    all_results = []
    for p in products:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(generate_full_package(p))
            loop.close()
            if isinstance(result, dict) and not result.get("error"):
                all_results.append({
                    "product": p,
                    "heading": result.get("header", "")[:50],
                    "description": result.get("description", ""),
                    "keywords": result.get("keywords", ""),
                    "hashtags": result.get("hashtags", "")
                })
            else:
                all_results.append({"product": p, "heading": "Ошибка генерации", "description": "", "keywords": "", "hashtags": ""})
        except Exception as e:
            all_results.append({"product": p, "heading": "Ошибка генерации", "description": "", "keywords": "", "hashtags": ""})

    xlsx_path = create_xlsx_file(all_results, 0)
    pdf_path = create_pdf_file(all_results, 0)
    failed = sum(1 for r in all_results if r["heading"] == "Ошибка генерации")
    message = f"Обработано {len(all_results)} товаров."
    if failed:
        message += f" Ошибок: {failed}."
    return jsonify({
        "message": message,
        "xlsx_file": os.path.basename(xlsx_path),
        "pdf_file": os.path.basename(pdf_path)
    })

@app.route("/download_file")
def download_file():
    fname = request.args.get("file")
    if not fname:
        return "Не указано имя файла", 400
    path = TEMP_DIR / fname
    if not path.exists():
        return "Файл не найден", 404
    return send_file(str(path), as_attachment=True, download_name=fname)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
