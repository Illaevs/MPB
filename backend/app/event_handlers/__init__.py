"""
Пакет in-process обработчиков событий (декораторно зарегистрированных
через `@on(...)` из `app.services.event_dispatcher`).

Сюда складываются по одному модулю на сущность/домен:
  contracts.py, documents.py, outgoing_documents.py, approvals.py, ...

Модули НЕ импортируются явно в этот __init__.py — за это отвечает
`event_dispatcher.discover_handlers()`, который вызывается на startup
и автоматически тянет всё содержимое пакета через pkgutil.

Декларативно регистрируем хендлеры так:

    from app.services.event_dispatcher import on, EventContext, Cancel, Continue, Mutate

    @on("contract.before_status_change", priority=100, can_cancel=True)
    async def validate_contract_status(ctx: EventContext):
        new = ctx.payload.get("status_after")
        if new == "signed" and not ctx.payload.get("signatories"):
            return Cancel("Нельзя подписать договор без подписантов")
        return Continue()
"""
