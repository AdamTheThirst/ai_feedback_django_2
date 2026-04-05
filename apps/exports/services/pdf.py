"""Сервис генерации PDF-экспорта результата диалога по требованиям макета."""

from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.pdfgen import canvas

from apps.analysis.services.results import build_dialog_results_view_model
from apps.dialogs.models import DialogSession


PDF_FONT_REGULAR = "AppRegular"
PDF_FONT_BOLD = "AppBold"


def ensure_pdf_fonts_registered() -> tuple[str, str]:
    """Регистрирует кириллические шрифты для PDF и возвращает их имена.

    Контекст использования:
    - вызывается перед генерацией PDF, чтобы исключить «квадратики» вместо текста;
    - использует DejaVu Sans из типовых Linux-путей, если файл доступен.

    Параметры:
    - отсутствуют.

    Возвращает:
    - кортеж `(regular_font_name, bold_font_name)` для стилей reportlab.

    Исключения и особые случаи:
    - если TTF-файлы недоступны, возвращает fallback `Helvetica/Helvetica-Bold`.

    Побочные эффекты:
    - регистрирует шрифты в глобальном реестре reportlab.
    """

    regular_path_candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/local/share/fonts/dejavu/DejaVuSans.ttf"),
    ]
    bold_path_candidates = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/local/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    ]
    regular_path = next((path for path in regular_path_candidates if path.exists()), None)
    bold_path = next((path for path in bold_path_candidates if path.exists()), None)
    if not regular_path or not bold_path:
        return "Helvetica", "Helvetica-Bold"

    registered = pdfmetrics.getRegisteredFontNames()
    if PDF_FONT_REGULAR not in registered:
        pdfmetrics.registerFont(TTFont(PDF_FONT_REGULAR, str(regular_path)))
    if PDF_FONT_BOLD not in registered:
        pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, str(bold_path)))
    return PDF_FONT_REGULAR, PDF_FONT_BOLD


class NumberedCanvas(canvas.Canvas):
    """Canvas с постраничной нумерацией в формате `n из A` в нижнем правом углу.

    Контекст использования:
    - применяется при финальной сборке PDF, чтобы подставить общее число страниц.

    Параметры:
    - принимает стандартные параметры `reportlab.pdfgen.canvas.Canvas`.

    Возвращает:
    - объект canvas с переопределённым `save` и `showPage`.

    Исключения и особые случаи:
    - отсутствуют.

    Побочные эффекты:
    - записывает страницы в выходной PDF-поток.
    """

    def __init__(self, *args, **kwargs):
        """Инициализирует canvas и буферизует состояния страниц.

        Контекст использования:
        - внутренний механизм реализации двухпроходной нумерации страниц.

        Параметры:
        - стандартные параметры базового canvas.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - создаёт внутренний список сохранённых состояний страниц.
        """

        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        """Сохраняет состояние текущей страницы и переходит к следующей.

        Контекст использования:
        - вызывается reportlab при завершении каждой страницы.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - добавляет состояние страницы в буфер `self._saved_page_states`.
        """

        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        """Проставляет нумерацию `n из A` на всех страницах и сохраняет документ.

        Контекст использования:
        - вызывается в конце сборки PDF.

        Параметры:
        - отсутствуют.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - записывает финальные байты PDF в выходной поток.
        """

        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_number(total_pages)
            super().showPage()
        super().save()

    def _draw_page_number(self, page_count: int) -> None:
        """Рисует подпись страницы внизу справа согласно требованиям макета.

        Контекст использования:
        - внутренний helper для `save`.

        Параметры:
        - `page_count`: общее число страниц документа.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - рисует текст на текущей странице canvas.
        """

        registered = pdfmetrics.getRegisteredFontNames()
        font_name = PDF_FONT_REGULAR if PDF_FONT_REGULAR in registered else "Helvetica"
        separator = "из" if font_name == PDF_FONT_REGULAR else "/"
        label = f"{self._pageNumber} {separator} {page_count}"
        self.setFont(font_name, 8)
        self.setFillColor(colors.HexColor("#A7A7A7"))
        x = A4[0] - 15 * mm - stringWidth(label, font_name, 8)
        y = 10 * mm
        self.drawString(x, y, label)


def build_result_pdf(dialog: DialogSession) -> bytes:
    """Генерирует PDF результата диалога в форматировании `PDF_LAYOUT_REQUIREMENTS`.

    Контекст использования:
    - вызывается endpoint-ом экспорта результата;
    - формирует единый документ для скачивания пользователем.

    Параметры:
    - `dialog`: диалог, по которому строится экспорт.

    Возвращает:
    - бинарный PDF-поток в виде `bytes`.

    Исключения и особые случаи:
    - если карточек анализа нет, выводится контролируемое техническое сообщение.

    Побочные эффекты:
    - отсутствуют.
    """

    view_model = build_dialog_results_view_model(dialog)
    regular_font_name, bold_font_name = ensure_pdf_fonts_registered()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"result-{dialog.public_id}",
    )

    styles = getSampleStyleSheet()
    primary = colors.HexColor("#004CDE")
    styles.add(
        ParagraphStyle(
            name="H1Blue",
            parent=styles["Heading1"],
            fontName=bold_font_name,
            fontSize=24,
            leading=28,
            textColor=primary,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2Blue",
            parent=styles["Heading2"],
            fontName=bold_font_name,
            fontSize=16,
            leading=20,
            textColor=primary,
        )
    )
    styles.add(ParagraphStyle(name="Big", parent=styles["Normal"], fontName=regular_font_name, fontSize=16, leading=20))
    styles.add(
        ParagraphStyle(
            name="BigBlueBold",
            parent=styles["Normal"],
            fontName=bold_font_name,
            fontSize=16,
            leading=20,
            textColor=primary,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["Normal"],
            fontName=regular_font_name,
            fontSize=12,
            leading=16,
            textColor=colors.black,
        )
    )

    story = []
    story.append(Paragraph("Результат тренажёра обратной связи", styles["H1Blue"]))
    story.append(Spacer(1, 6))

    def add_meta_line(label: str, value: str) -> None:
        """Добавляет мета-строку в верхнюю часть PDF.

        Контекст использования:
        - вспомогательная функция при формировании шапки документа.

        Параметры:
        - `label`: заголовок поля;
        - `value`: значение поля.

        Возвращает:
        - ничего не возвращает.

        Исключения и особые случаи:
        - отсутствуют.

        Побочные эффекты:
        - добавляет абзац в массив `story`.
        """

        story.append(Paragraph(f'<font color="#004CDE"><b>{label}</b></font> {value}', styles["Big"]))

    add_meta_line("Игра:", dialog.game.title if dialog.game else "—")
    add_meta_line("Сценарий:", dialog.scenario.title if dialog.scenario else "—")
    add_meta_line("Дата и время старта:", dialog.started_at.strftime("%d.%m.%Y %H:%M:%S UTC"))
    add_meta_line("Причина завершения:", dialog.get_ended_reason_display() or "—")
    story.append(Spacer(1, 6))
    story.append(Paragraph(f'<font color="#004CDE"><b>Сумма баллов: {view_model["total_score"]} из {view_model["max_score"]}</b></font>', styles["Big"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Карточки анализа", styles["H1Blue"]))
    story.append(Spacer(1, 6))

    cards = view_model["cards"]
    if not cards:
        story.append(Paragraph(view_model["empty_state_message"], styles["Body"]))
    else:
        for index, card in enumerate(cards, start=1):
            story.append(
                Paragraph(
                    f'{index}. {card.title_snapshot} ({card.rating} из {card.rating_max})',
                    styles["H2Blue"],
                )
            )
            story.append(Paragraph(card.header_snapshot_text or "", styles["Body"]))
            if card.comment_snapshot_text:
                story.append(Paragraph(card.comment_snapshot_text, styles["Body"]))
            story.append(Paragraph(card.analysis_text, styles["Body"]))
            story.append(Spacer(1, 6))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Транскрипт диалога", styles["H1Blue"]))
    story.append(Spacer(1, 6))

    for msg in dialog.messages.order_by("sequence_no", "id"):
        role = "Пользователь" if msg.role == "user" else "Персонаж"
        story.append(Paragraph(f"<b>{role}:</b> {msg.text}", styles["Body"]))
        story.append(Spacer(1, 3))

    doc.build(story, canvasmaker=NumberedCanvas)
    return buffer.getvalue()
