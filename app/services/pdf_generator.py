"""Генератор PDF-смет через WeasyPrint."""

import logging
import uuid
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

from app.core.config import settings
from app.schemas.calculation import CalculationData
from app.services.calculator import calculate_total_cost


logger = logging.getLogger(__name__)


class PDFGenerator:
    """Генератор PDF-смет."""

    def __init__(self):
        """Инициализация генератора."""
        self.templates_dir = Path("app/templates/pdf")
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

        self.env = Environment(
            loader=FileSystemLoader(self.templates_dir),
            autoescape=True
        )

    async def generate_estimate(
        self,
        calculation_data: CalculationData,
        user_info: dict[str, str]
    ) -> Path:
        """Генерирует PDF-смету из данных расчёта.

        Args:
            calculation_data: Данные расчёта
            user_info: Информация о пользователе

        Returns:
            Путь к сгенерированному PDF файлу
        """
        try:
            # Генерация уникального ID
            calc_id = str(uuid.uuid4())[:8].upper()

            # Расчёт стоимости
            costs = calculate_total_cost(calculation_data)

            # Подготовка данных для шаблона
            fabric_names = {
                "msd": "MSD",
                "bauf": "BAUF"
            }
            profile_names = {
                "insert": "Со вставкой",
                "shadow_eco": "Теневой ЭКОНОМ",
                "shadow_eurokraab": "Теневой EuroKraab",
                "floating": "Парящий",
                "am1": "Однородный AM1"
            }
            cornice_names = {
                "pk14_2m": "ПК-14 (2 м)",
                "pk14_3_2m": "ПК-14 (3.2 м)",
                "pk14_3_6m": "ПК-14 (3.6 м)",
                "pk5": "ПК-5",
                "bp40": "БП-40"
            }

            # Дополнительные углы
            extra_corners = 0
            corner_price = 0
            if calculation_data.profile_type == "insert":
                extra_corners = max(0, calculation_data.corners - 4)
                corner_price = settings.profile_insert_extra_corner_price
            elif calculation_data.profile_type in ["shadow_eurokraab", "floating"]:
                extra_corners = calculation_data.corners
                corner_price = (
                    settings.profile_shadow_eurokraab_corner_price
                    if calculation_data.profile_type == "shadow_eurokraab"
                    else settings.profile_floating_corner_price
                )

            template_data = {
                "date": datetime.now().strftime("%d.%m.%Y"),
                "calculation_id": calc_id,
                "phone": settings.contact_phone,
                "telegram": settings.contact_telegram,
                "area": calculation_data.area,
                "perimeter": calculation_data.perimeter,
                "corners": calculation_data.corners,
                "fabric_type": fabric_names.get(calculation_data.fabric_type, calculation_data.fabric_type),
                "fabric_price": (
                    settings.fabric_msd_price if calculation_data.fabric_type == "msd"
                    else settings.fabric_bauf_price
                ),
                "fabric_total": costs["fabric_total"],
                "profile_type": profile_names.get(calculation_data.profile_type, calculation_data.profile_type),
                "profile_price": (
                    0 if calculation_data.profile_type == "insert"
                    else (
                        settings.profile_shadow_eco_price if calculation_data.profile_type == "shadow_eco"
                        else (
                            settings.profile_shadow_eurokraab_price if calculation_data.profile_type == "shadow_eurokraab"
                            else (
                                settings.profile_floating_price if calculation_data.profile_type == "floating"
                                else settings.profile_am1_price
                            )
                        )
                    )
                ),
                "profile_base": costs["profile_base"],
                "extra_corners": extra_corners,
                "corner_price": corner_price,
                "corners_total": costs["corners_total"],
                "profile_total": costs["profile_total"],
                "cornices": calculation_data.has_cornices,
                "cornice_type": (
                    cornice_names.get(calculation_data.cornice_type, calculation_data.cornice_type)
                    if calculation_data.cornice_type else None
                ),
                "cornice_total": costs["cornice_total"],
                "spotlights": calculation_data.spotlights,
                "spotlights_total": costs["spotlights_total"],
                "ceramic_area": calculation_data.ceramic_area,
                "ceramic_total": costs["ceramic_total"],
                "chandeliers": calculation_data.chandeliers,
                "chandeliers_total": costs["chandeliers_total"],
                "lighting_total": costs["lighting_total"],
                "total_cost": costs["total_cost"],
            }

            # Рендер HTML
            template = self.env.get_template("calculation.html")
            html_content = template.render(**template_data)

            # Генерация PDF
            output_path = self.output_dir / f"estimate_{calc_id}.pdf"

            html = HTML(string=html_content)
            css_path = self.templates_dir / "styles.css"
            css = CSS(filename=str(css_path)) if css_path.exists() else None

            stylesheets = [css] if css else []
            html.write_pdf(
                target=str(output_path),
                stylesheets=stylesheets
            )

            logger.info(f"PDF сгенерирован: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка генерации PDF: {e}", exc_info=True)
            raise


async def cleanup_old_pdfs(max_age_hours: int = 24) -> None:
    """Удаляет PDF старше указанного времени.

    Args:
        max_age_hours: Максимальный возраст файла в часах
    """
    output_dir = Path("output")
    if not output_dir.exists():
        return

    now = datetime.now()
    deleted_count = 0

    for pdf_file in output_dir.glob("*.pdf"):
        try:
            file_age = now - datetime.fromtimestamp(pdf_file.stat().st_mtime)
            if file_age.total_seconds() > max_age_hours * 3600:
                pdf_file.unlink()
                deleted_count += 1
        except Exception as e:
            logger.warning(f"Не удалось удалить файл {pdf_file}: {e}")

    if deleted_count > 0:
        logger.info(f"Удалено {deleted_count} старых PDF файлов")


# Глобальный экземпляр
pdf_generator = PDFGenerator()

