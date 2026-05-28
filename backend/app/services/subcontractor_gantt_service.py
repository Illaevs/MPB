"""
Gantt service for subcontractor stage scheduling.
"""
import uuid
from calendar import monthrange
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import SubcontractorStage, SubcontractorStageDependency
from app.models.stage_dependency import normalize_dependency_type


class SubcontractorGanttService:
    @staticmethod
    def is_workday(check_date: date) -> bool:
        return check_date.weekday() < 5

    @staticmethod
    def _normalize_uuid(value: Any) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

    @staticmethod
    def add_workdays(start_date: date, workdays: int) -> date:
        current_date = start_date
        added_days = 0
        while added_days < workdays:
            current_date += timedelta(days=1)
            if SubcontractorGanttService.is_workday(current_date):
                added_days += 1
        return current_date

    @staticmethod
    def subtract_workdays(end_date: date, workdays: int) -> date:
        current_date = end_date
        subtracted_days = 0
        while subtracted_days < workdays:
            current_date -= timedelta(days=1)
            if SubcontractorGanttService.is_workday(current_date):
                subtracted_days += 1
        return current_date

    @staticmethod
    def add_months(start_date: date, months: int) -> date:
        month_index = (start_date.month - 1) + months
        target_year = start_date.year + (month_index // 12)
        target_month = (month_index % 12) + 1
        target_day = min(start_date.day, monthrange(target_year, target_month)[1])
        return date(target_year, target_month, target_day)

    @classmethod
    def calculate_end_date(cls, start_date: date, duration: int, term_type: str) -> date:
        normalized_duration = max(int(duration or 1), 1)
        if term_type == "work_days":
            return cls.add_workdays(start_date, normalized_duration)
        if term_type == "week":
            return start_date + timedelta(days=(normalized_duration * 7))
        if term_type == "month":
            return cls.add_months(start_date, normalized_duration)
        return start_date + timedelta(days=normalized_duration)

    @classmethod
    def calculate_start_date_from_end(cls, end_date: date, duration: int, term_type: str) -> date:
        normalized_duration = max(int(duration or 1), 1)
        if term_type == "work_days":
            return cls.subtract_workdays(end_date, normalized_duration)
        if term_type == "week":
            return end_date - timedelta(days=(normalized_duration * 7))
        if term_type == "month":
            return cls.add_months(end_date, -normalized_duration)
        return end_date - timedelta(days=normalized_duration)

    @staticmethod
    def resolve_effective_end_date(
        stage: Optional[SubcontractorStage],
        fallback_end: Optional[date] = None,
    ) -> Optional[date]:
        if stage is None:
            return fallback_end
        if stage.close_date and getattr(stage, "status", None) == "completed":
            return stage.close_date
        return fallback_end or stage.date_end or stage.date_start

    @classmethod
    def _calculate_dependency_candidate_start(
        cls,
        dependency: SubcontractorStageDependency,
        successor: SubcontractorStage,
    ) -> Optional[date]:
        predecessor = dependency.predecessor
        if predecessor is None:
            return None

        lag_days = int(dependency.lag or 0)
        dependency_type = normalize_dependency_type(dependency.dependency_type)
        predecessor_start = predecessor.date_start
        predecessor_end = cls.resolve_effective_end_date(predecessor)

        if dependency_type == "SS":
            if predecessor_start is None:
                return None
            return predecessor_start + timedelta(days=lag_days)

        if dependency_type == "FF":
            if predecessor_end is None:
                return None
            successor_end = predecessor_end + timedelta(days=lag_days)
            return cls.calculate_start_date_from_end(successor_end, successor.duration, successor.term_type)

        if dependency_type == "SF":
            if predecessor_start is None:
                return None
            successor_end = predecessor_start + timedelta(days=lag_days)
            return cls.calculate_start_date_from_end(successor_end, successor.duration, successor.term_type)

        if predecessor_end is None:
            return None
        return predecessor_end + timedelta(days=lag_days)

    @classmethod
    async def _resolve_successor_schedule(
        cls,
        successor: SubcontractorStage,
        db: AsyncSession,
    ) -> Optional[Tuple[date, date]]:
        query = select(SubcontractorStageDependency).where(
            SubcontractorStageDependency.successor_id == successor.id
        ).options(
            selectinload(SubcontractorStageDependency.predecessor)
        )

        result = await db.execute(query)
        dependencies = result.scalars().all()

        candidate_starts: List[date] = []
        stale_dependency_ids: List[uuid.UUID] = []

        for dependency in dependencies:
            if dependency.predecessor is None:
                stale_dependency_ids.append(dependency.id)
                continue

            candidate_start = cls._calculate_dependency_candidate_start(dependency, successor)
            if candidate_start is not None:
                candidate_starts.append(candidate_start)

        if stale_dependency_ids:
            await db.execute(
                delete(SubcontractorStageDependency).where(
                    SubcontractorStageDependency.id.in_(stale_dependency_ids)
                )
            )

        if not candidate_starts:
            if successor.date_start is None:
                return None
            resolved_start = successor.date_start
        else:
            resolved_start = max(candidate_starts)

        resolved_end = cls.calculate_end_date(
            resolved_start,
            successor.duration,
            successor.term_type,
        )
        return resolved_start, resolved_end

    @staticmethod
    def _record_affected_stage(
        affected_stages: List[Dict[str, Any]],
        stage: SubcontractorStage,
        date_start: date,
        date_end: date,
        effective_end_date: Optional[date],
    ) -> None:
        payload = {
            "id": str(stage.id),
            "name": stage.name,
            "date_start": date_start.isoformat(),
            "date_end": date_end.isoformat(),
            "effective_end_date": effective_end_date.isoformat() if effective_end_date else None,
        }

        for index, existing in enumerate(affected_stages):
            if existing["id"] == payload["id"]:
                affected_stages[index] = payload
                return

        affected_stages.append(payload)

    @classmethod
    async def get_stage_with_dependencies(
        cls,
        stage_id: uuid.UUID,
        db: AsyncSession,
    ) -> Optional[SubcontractorStage]:
        stage_uuid = cls._normalize_uuid(stage_id)
        query = select(SubcontractorStage).where(SubcontractorStage.id == stage_uuid).options(
            selectinload(SubcontractorStage.dependencies),
            selectinload(SubcontractorStage.dependents),
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def propagate_dates(
        cls,
        stage_id: uuid.UUID,
        new_start_date: Optional[date],
        new_duration: Optional[int],
        db: AsyncSession,
    ) -> Dict[str, Any]:
        stage_uuid = cls._normalize_uuid(stage_id)
        stage = await cls.get_stage_with_dependencies(stage_uuid, db)
        if not stage:
            raise ValueError(f"Stage with id {stage_id} not found")

        updated_start = new_start_date if new_start_date is not None else stage.date_start
        updated_duration = new_duration if new_duration is not None else stage.duration
        new_end_date = cls.calculate_end_date(updated_start, updated_duration, stage.term_type)

        await db.execute(
            update(SubcontractorStage).where(SubcontractorStage.id == stage_uuid).values(
                date_start=updated_start,
                duration=updated_duration,
                date_end=new_end_date,
            )
        )

        affected_stages: List[Dict[str, Any]] = []
        active_path = {stage_uuid}
        effective_end = cls.resolve_effective_end_date(stage, new_end_date)
        await cls._update_successors(stage_uuid, updated_start, effective_end, db, affected_stages, active_path)

        await db.commit()

        return {
            "updated_stage": {
                "id": str(stage_id),
                "name": stage.name,
                "date_start": updated_start.isoformat(),
                "date_end": new_end_date.isoformat(),
                "effective_end_date": effective_end.isoformat() if effective_end else None,
                "duration": updated_duration,
            },
            "affected_stages_count": len(affected_stages),
            "affected_stages": affected_stages,
        }

    @classmethod
    async def _update_successors(
        cls,
        predecessor_id: uuid.UUID,
        predecessor_start: date,
        predecessor_end: date,
        db: AsyncSession,
        affected_stages: List[Dict[str, Any]],
        visited: set,
    ) -> None:
        predecessor_uuid = cls._normalize_uuid(predecessor_id)
        query = select(SubcontractorStageDependency).where(
            SubcontractorStageDependency.predecessor_id == predecessor_uuid
        ).options(
            selectinload(SubcontractorStageDependency.successor).selectinload(SubcontractorStage.dependencies)
        )

        result = await db.execute(query)
        dependencies = result.scalars().all()

        for dependency in dependencies:
            successor = dependency.successor
            if successor is None:
                await db.execute(
                    delete(SubcontractorStageDependency).where(
                        SubcontractorStageDependency.id == dependency.id
                    )
                )
                continue

            if successor.id in visited:
                continue

            resolved_schedule = await cls._resolve_successor_schedule(successor, db)
            if resolved_schedule is None:
                continue

            new_successor_start, new_successor_end = resolved_schedule

            await db.execute(
                update(SubcontractorStage).where(SubcontractorStage.id == successor.id).values(
                    date_start=new_successor_start,
                    date_end=new_successor_end,
                )
            )

            effective_successor_end = cls.resolve_effective_end_date(successor, new_successor_end)
            cls._record_affected_stage(
                affected_stages,
                successor,
                new_successor_start,
                new_successor_end,
                effective_successor_end,
            )

            visited.add(successor.id)
            try:
                await cls._update_successors(
                    successor.id,
                    new_successor_start,
                    effective_successor_end,
                    db,
                    affected_stages,
                    visited,
                )
            finally:
                visited.remove(successor.id)

    @classmethod
    async def get_gantt_tree(cls, card_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
        try:
            card_uuid = cls._normalize_uuid(card_id)
        except Exception:
            card_uuid = None

        card_id_str = str(card_uuid) if card_uuid else str(card_id)
        card_id_hex = card_uuid.hex if card_uuid else None
        conditions = [SubcontractorStage.subcontractor_card_id == card_id_str]
        if card_id_hex:
            conditions.append(SubcontractorStage.subcontractor_card_id == card_id_hex)

        query = select(SubcontractorStage).where(or_(*conditions)).options(
            selectinload(SubcontractorStage.dependencies),
            selectinload(SubcontractorStage.dependents),
            selectinload(SubcontractorStage.subcontractor),
        ).order_by(SubcontractorStage.parent_id, SubcontractorStage.date_start)

        result = await db.execute(query)
        stages = result.scalars().all()

        stage_dict = {stage.id: stage for stage in stages}
        root_stages = []

        for stage in stages:
            if stage.parent_id is None:
                root_stages.append(stage)
            else:
                parent = stage_dict.get(stage.parent_id)
                if parent and not hasattr(parent, "children"):
                    parent.children = []
                if parent:
                    parent.children.append(stage)

        def serialize_stage(stage: SubcontractorStage) -> Dict[str, Any]:
            result = {
                "id": str(stage.id),
                "name": stage.name,
                "date_start": stage.date_start.isoformat() if stage.date_start else None,
                "date_end": stage.date_end.isoformat() if stage.date_end else None,
                "close_date": stage.close_date.isoformat() if stage.close_date else None,
                "duration": stage.duration,
                "status": stage.status,
                "type": stage.stage_type,
                "term_type": stage.term_type,
                "planned_cost": stage.planned_cost,
                "actual_cost": stage.actual_cost,
                "subcontractor": {
                    "id": str(stage.subcontractor.id) if stage.subcontractor else None,
                    "name": stage.subcontractor.name if stage.subcontractor else None,
                }
                if stage.subcontractor
                else None,
                "dependencies": [
                    {
                        "predecessor_id": str(dep.predecessor_id),
                        "successor_id": str(dep.successor_id),
                    "type": normalize_dependency_type(dep.dependency_type),
                        "lag": dep.lag,
                    }
                    for dep in stage.dependencies
                ],
                "children": [],
            }

            if hasattr(stage, "children"):
                result["children"] = [serialize_stage(child) for child in stage.children]

            return result

        return {
            "subcontractor_card_id": card_id_str,
            "stages": [serialize_stage(stage) for stage in root_stages],
        }
