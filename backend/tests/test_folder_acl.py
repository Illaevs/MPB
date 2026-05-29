"""Тесты для services/folder_acl.py — Этап 1 плана per-folder ACL.

Покрывают:
  - чистые функции: normalize_path, path_ancestors, is_entity_path
  - effective_perms() golden cases на in-memory SQLite (async)

Запуск:
  pip install pytest pytest-asyncio
  cd backend && python -m pytest tests/test_folder_acl.py -v

Не покрываются здесь (на следующих этапах):
  - роутер file_folder_permissions (Этап 3)
  - интеграция в files_catalog (Этап 2 — это integration test)
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import pytest
import pytest_asyncio

# Allow `from app...` imports when running tests from any directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.base import Base
from app.models import FileFolderPermission, User, Role  # noqa: F401
from app.services.folder_acl import (
    ALL_PERMS,
    Perm,
    effective_perms,
    grant_creator_manage_perms,
    is_entity_path,
    normalize_path,
    path_ancestors,
)


# ────────────────────────────────────────────────────────────────────
# Pure function tests (no DB needed)
# ────────────────────────────────────────────────────────────────────


class TestNormalizePath:
    """Канонический вид путей: ведущий и завершающий '/', схлопнутые
    дубли, обработка '.' и '..'."""

    def test_empty_and_none(self):
        assert normalize_path(None) == "/"
        assert normalize_path("") == "/"
        assert normalize_path("   ") == "/"

    def test_root(self):
        assert normalize_path("/") == "/"

    def test_simple_folder(self):
        assert normalize_path("/foo") == "/foo/"
        assert normalize_path("/foo/") == "/foo/"
        assert normalize_path("foo") == "/foo/"
        assert normalize_path("foo/") == "/foo/"

    def test_nested(self):
        assert normalize_path("/foo/bar/baz") == "/foo/bar/baz/"
        assert normalize_path("/foo/bar/baz/") == "/foo/bar/baz/"

    def test_collapses_double_slash(self):
        assert normalize_path("//foo//bar//") == "/foo/bar/"
        assert normalize_path("///") == "/"

    def test_backslash_normalized(self):
        # Windows-friendly: backslash → slash.
        assert normalize_path("\\foo\\bar") == "/foo/bar/"

    def test_dot_segments_dropped(self):
        assert normalize_path("/foo/./bar/") == "/foo/bar/"
        assert normalize_path("/./foo/./") == "/foo/"

    def test_dotdot_pops(self):
        assert normalize_path("/foo/bar/../baz/") == "/foo/baz/"
        assert normalize_path("/foo/../") == "/"
        # Защита от подъёма выше корня — лишние '..' просто игнорируем.
        assert normalize_path("/../../foo") == "/foo/"

    def test_unicode(self):
        # Кириллица в пути — ничего не должно ломаться.
        assert normalize_path("/Архив/2026/") == "/Архив/2026/"


class TestPathAncestors:
    """Список предков для одного SQL `IN` в effective_perms."""

    def test_root(self):
        assert path_ancestors("/") == ["/"]

    def test_single_level(self):
        assert path_ancestors("/foo/") == ["/", "/foo/"]

    def test_deep(self):
        assert path_ancestors("/a/b/c/") == [
            "/", "/a/", "/a/b/", "/a/b/c/"
        ]

    def test_normalizes_first(self):
        # На вход неканонический путь — функция сама нормализует.
        assert path_ancestors("a/b") == ["/", "/a/", "/a/b/"]


class TestIsEntityPath:
    """Точно знаем, какие префиксы переключают логику на storage_authz."""

    def test_root_is_not_entity(self):
        assert not is_entity_path("/")

    def test_free_folder_is_not_entity(self):
        assert not is_entity_path("/Архив/")
        assert not is_entity_path("/Архив/2026/01/")
        assert not is_entity_path("/shared/")

    def test_deals_is_entity(self):
        assert is_entity_path("/deals/abc-123/")
        assert is_entity_path("/deals/abc-123/files/2026/")

    def test_contracts_is_entity(self):
        assert is_entity_path("/contracts/x/")

    def test_legal_work_is_entity(self):
        # Обе формы — с дефисом и подчёркиванием — на всякий случай.
        assert is_entity_path("/legal-work/case-1/")
        assert is_entity_path("/legal_work/case-1/")

    def test_subcontractor_variants(self):
        assert is_entity_path("/subcontractor/x/")
        assert is_entity_path("/subcontractors/x/")

    def test_tasks_is_entity(self):
        # /_tasks/{task_id} — папка вложений задачи.
        assert is_entity_path("/_tasks/abc-123/")


# ────────────────────────────────────────────────────────────────────
# effective_perms tests (in-memory async SQLite)
# ────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def db_session():
    """In-memory SQLite + async session. Каждый тест получает чистую БД."""
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", echo=False
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as sess:
        yield sess

    await engine.dispose()


def _make_user(user_id="u1", role_id="r1", is_superuser=False):
    """Не использует ORM (нужно только для duck-typing в effective_perms)."""

    class _StubUser:
        pass

    u = _StubUser()
    u.id = user_id
    u.role_id = role_id
    u.is_superuser = is_superuser
    return u


async def _seed_rule(
    db,
    *,
    folder_path,
    principal_type="user",
    principal_id="u1",
    read=False,
    write=False,
    delete=False,
    manage=False,
    inherit=True,
):
    rule = FileFolderPermission(
        folder_path=normalize_path(folder_path),
        principal_type=principal_type,
        principal_id=principal_id,
        can_read=read,
        can_write=write,
        can_delete=delete,
        can_manage_perms=manage,
        inherit_to_subfolders=inherit,
        created_by_user_id="u1",
    )
    db.add(rule)
    await db.flush()
    return rule


class TestEffectivePerms:
    """Golden cases для effective_perms() — основная логика резолва."""

    @pytest.mark.asyncio
    async def test_superuser_always_full(self, db_session, monkeypatch):
        # Замокать _section_fallback не нужно — суперюзер обходит её.
        u = _make_user(is_superuser=True)
        perms = await effective_perms(db_session, u, "/anywhere/")
        assert perms == ALL_PERMS

    @pytest.mark.asyncio
    async def test_entity_path_delegates_to_storage_authz(
        self, db_session, monkeypatch
    ):
        # storage_authz._entity_path_perms — фейкаем через monkeypatch.
        from app.services import folder_acl

        async def _fake_entity_perms(db, user, p):
            return {Perm.READ, Perm.WRITE, Perm.DELETE}

        monkeypatch.setattr(folder_acl, "_entity_path_perms", _fake_entity_perms)

        u = _make_user()
        perms = await effective_perms(db_session, u, "/deals/abc/files/")
        assert perms == {Perm.READ, Perm.WRITE, Perm.DELETE}
        # MANAGE на entity-path НЕ выдаётся через storage_authz.
        assert Perm.MANAGE not in perms

    @pytest.mark.asyncio
    async def test_no_rules_falls_back_to_section(self, db_session, monkeypatch):
        from app.services import folder_acl

        async def _fake_section(db, user, section="files_catalog"):
            return {Perm.READ}

        monkeypatch.setattr(folder_acl, "_section_fallback", _fake_section)

        u = _make_user()
        perms = await effective_perms(db_session, u, "/Архив/")
        assert perms == {Perm.READ}

    @pytest.mark.asyncio
    async def test_explicit_rule_on_target(self, db_session, monkeypatch):
        from app.services import folder_acl

        async def _fake_section(*a, **k):
            return set()  # sentinel: если правил нет, ничего не возвращаем

        monkeypatch.setattr(folder_acl, "_section_fallback", _fake_section)

        await _seed_rule(
            db_session, folder_path="/Архив/", read=True, write=True, inherit=False
        )

        u = _make_user()
        perms = await effective_perms(db_session, u, "/Архив/")
        assert perms == {Perm.READ, Perm.WRITE}

    @pytest.mark.asyncio
    async def test_parent_rule_with_inherit_applies_to_child(
        self, db_session, monkeypatch
    ):
        from app.services import folder_acl

        monkeypatch.setattr(
            folder_acl,
            "_section_fallback",
            lambda *a, **k: _coroutine_returning(set()),
        )

        await _seed_rule(
            db_session, folder_path="/Архив/", read=True, inherit=True
        )

        u = _make_user()
        perms = await effective_perms(db_session, u, "/Архив/2026/01/")
        assert Perm.READ in perms

    @pytest.mark.asyncio
    async def test_parent_rule_without_inherit_does_not_apply_to_child(
        self, db_session, monkeypatch
    ):
        from app.services import folder_acl

        monkeypatch.setattr(
            folder_acl,
            "_section_fallback",
            lambda *a, **k: _coroutine_returning(set()),
        )

        await _seed_rule(
            db_session, folder_path="/Архив/", read=True, inherit=False
        )

        u = _make_user()
        # На самой /Архив/ — есть read; на /Архив/2026/ — уже нет
        # (потому что inherit=False).
        perms_self = await effective_perms(db_session, u, "/Архив/")
        perms_child = await effective_perms(db_session, u, "/Архив/2026/")
        assert Perm.READ in perms_self
        assert Perm.READ not in perms_child

    @pytest.mark.asyncio
    async def test_role_rule_applies_to_user_with_that_role(
        self, db_session, monkeypatch
    ):
        from app.services import folder_acl

        monkeypatch.setattr(
            folder_acl,
            "_section_fallback",
            lambda *a, **k: _coroutine_returning(set()),
        )

        await _seed_rule(
            db_session,
            folder_path="/shared/",
            principal_type="role",
            principal_id="role-x",
            read=True,
            write=True,
        )

        u = _make_user(role_id="role-x")
        perms = await effective_perms(db_session, u, "/shared/")
        assert perms == {Perm.READ, Perm.WRITE}

    @pytest.mark.asyncio
    async def test_user_and_role_rules_union(self, db_session, monkeypatch):
        from app.services import folder_acl

        monkeypatch.setattr(
            folder_acl,
            "_section_fallback",
            lambda *a, **k: _coroutine_returning(set()),
        )

        # Через role: read.
        await _seed_rule(
            db_session,
            folder_path="/shared/",
            principal_type="role",
            principal_id="role-x",
            read=True,
        )
        # Через user: write.
        await _seed_rule(
            db_session,
            folder_path="/shared/",
            principal_type="user",
            principal_id="u1",
            write=True,
        )

        u = _make_user(user_id="u1", role_id="role-x")
        perms = await effective_perms(db_session, u, "/shared/")
        assert perms == {Perm.READ, Perm.WRITE}

    @pytest.mark.asyncio
    async def test_request_scope_cache_reuses_result(self, db_session):
        """Дважды вызывая effective_perms с одним request — БД должна
        получить запрос только один раз."""

        from app.services import folder_acl
        from types import SimpleNamespace

        # Stub request с request.state.
        request = SimpleNamespace(state=SimpleNamespace())

        u = _make_user(is_superuser=True)  # superuser ветка — без БД-запросов
        r1 = await effective_perms(db_session, u, "/foo/", request=request)
        r2 = await effective_perms(db_session, u, "/foo/", request=request)
        assert r1 == r2 == ALL_PERMS
        # Кэш на месте:
        assert "/foo/" in request.state._folder_acl_cache


class TestGrantCreatorManagePerms:
    """Авто-вставка правила creator-as-manager при mkdir."""

    @pytest.mark.asyncio
    async def test_inserts_rule_for_creator(self, db_session):
        u = _make_user(user_id="u1")
        rule = await grant_creator_manage_perms(db_session, u, "/Архив/")
        assert rule is not None
        assert rule.principal_id == "u1"
        assert rule.principal_type == "user"
        assert rule.can_manage_perms is True
        assert rule.inherit_to_subfolders is False

    @pytest.mark.asyncio
    async def test_idempotent(self, db_session):
        u = _make_user(user_id="u1")
        r1 = await grant_creator_manage_perms(db_session, u, "/Архив/")
        r2 = await grant_creator_manage_perms(db_session, u, "/Архив/")
        # При повторном вызове возвращает существующее правило, не дублирует.
        assert r1.id == r2.id

    @pytest.mark.asyncio
    async def test_skips_entity_path(self, db_session):
        u = _make_user(user_id="u1")
        rule = await grant_creator_manage_perms(db_session, u, "/deals/abc/")
        # На entity-path правило НЕ вставляется (продуктовое решение).
        assert rule is None

    @pytest.mark.asyncio
    async def test_skips_root(self, db_session):
        u = _make_user(user_id="u1")
        rule = await grant_creator_manage_perms(db_session, u, "/")
        assert rule is None

    @pytest.mark.asyncio
    async def test_skips_superuser(self, db_session):
        u = _make_user(is_superuser=True)
        rule = await grant_creator_manage_perms(db_session, u, "/Архив/")
        # Суперу не нужны формальные записи.
        assert rule is None


# ────────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────────


def _coroutine_returning(value):
    """Возвращает coroutine, отдающую value. Удобно для monkeypatch
    async-функций обычным lambda."""

    async def _f(*a, **k):
        return value

    return _f()
