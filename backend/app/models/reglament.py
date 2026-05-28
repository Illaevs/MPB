"""
Reglament + ReglamentSection — модели нормативной базы (СНиП/ГОСТ/СП/ФЗ).

Изолированный домен: отдельный от основной CRM-индексации. Используется
для bootstrap-нормативки генпроектирования (СП 63.13330, СП 16.13330,
ГОСТ 27751, и т.п.). Поиск через `routers/reglaments.py:search` (не через
основной `routers/search.py`) — намеренное разделение, чтобы нормативка
не «забивала» поиск по бизнес-данным.

Связь с embeddings: каждая `ReglamentSection` имеет 0..1 запись в
`reglament_embeddings` (BLOB), индексация через bge-m3 раз в bootstrap
или по запросу (нормы меняются редко).

Статусы документа:
  • actual               — действует
  • partially_actual     — частично действует (отдельные пункты заменены)
  • replaced             — заменён новой редакцией (см. `replaced_by_id`)
  • cancelled            — отменён без замены
"""
import uuid

from sqlalchemy import Column, String, Date, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Reglament(Base):
    """Нормативный документ-header: СП 63.13330.2018 «Бетонные и
    железобетонные конструкции».

    Сам контент хранится в `ReglamentSection` (по разделам). Здесь —
    только метаданные документа.
    """
    __tablename__ = "reglaments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Тип документа — СП / ГОСТ / СНиП / ФЗ / ПП (постановление правительства).
    doc_type = Column(String(16), nullable=False, index=True)

    # Номер документа без типа — "63.13330.2018", "27751-2014", "II-3-79".
    # Уникальность — (doc_type, doc_number).
    doc_number = Column(String(64), nullable=False, index=True)

    # Короткий title — «Бетонные и железобетонные конструкции».
    title = Column(String(512), nullable=False)
    # Полное название документа со ссылкой на родительский номер если есть.
    full_title = Column(Text)

    # Статус действия (см. docstring модуля).
    status = Column(String(32), nullable=False, default="actual", index=True)

    # Даты ввода в действие и отмены.
    effective_date = Column(Date)
    cancelled_date = Column(Date)

    # Если документ заменён новой редакцией — ссылка на актуальный.
    replaced_by_id = Column(String(36), ForeignKey("reglaments.id", ondelete="SET NULL"))

    # Дисциплины через запятую: "КЖ,КМ,АР,ОВ" — для фильтра в каталоге.
    # CSV намеренно (а не отдельная таблица) — теги предопределены,
    # количество <10, удобнее для UI-фильтра.
    discipline_tags = Column(String(256))

    # Откуда взяли (для прослеживаемости): docs.cntd.ru/document/...
    source_url = Column(String(512))

    # Статистика — для отображения в каталоге без JOIN'а.
    page_count = Column(Integer)
    section_count = Column(Integer, default=0)
    full_text_size = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    sections = relationship(
        "ReglamentSection",
        back_populates="reglament",
        cascade="all, delete-orphan",
        order_by="ReglamentSection.order_idx",
    )


class ReglamentSection(Base):
    """Раздел/пункт нормативного документа — единица индексации.

    Каждая секция — отдельная запись в FTS5 + embedding. При поиске
    результаты — это секции (не документы целиком), с breadcrumb до
    родительской нормы (СП 63.13330.2018 → п. 5.4.2).
    """
    __tablename__ = "reglament_sections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    reglament_id = Column(
        String(36),
        ForeignKey("reglaments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Иерархический номер: "1", "1.2", "5.4.2", "Приложение А", "Введение".
    # Текстовый, потому что встречаются нестандартные нумерации (приложения).
    section_number = Column(String(32))

    # Заголовок раздела/пункта: «Защитный слой бетона для арматуры».
    section_title = Column(String(512))

    # Тело раздела — то что индексируется FTS5 и embedding'ом.
    content = Column(Text, nullable=False)

    # Иерархия: ссылка на родительский раздел (5.4 → 5.4.2).
    # Для построения хлебных крошек и оглавления.
    parent_section_id = Column(
        String(36),
        ForeignKey("reglament_sections.id", ondelete="CASCADE"),
    )

    # Порядок для устойчивого ORDER BY (потому что 1.10 vs 1.2 ASCII-sort
    # некорректен — нужен явный order).
    order_idx = Column(Integer, nullable=False, default=0)

    # Длина контента для статистики/прогресса bootstrap'а.
    char_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    reglament = relationship("Reglament", back_populates="sections")
