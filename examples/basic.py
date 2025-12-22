"""
This example demonstrates most basic operations with single model
"""

from tortoise import Model, fields


class Event(Model):
    id = fields.IntField(primary_key=True)
    name = fields.TextField()
    datetime = fields.DatetimeField(null=True)

    class Meta:
        table = "event"

    def __str__(self) -> str:
        return self.name


async def run() -> None:
    event = await Event.create(name="Test")
    await Event.filter(id=event.id).update(name="Updated name")

    print(await Event.filter(name="Updated name").first())
    # >>> Updated name

    await Event(name="Test 2").save()
    print(await Event.all().values_list("id", flat=True))
    # >>> [1, 2]
    print(await Event.all().values("id", "name"))
    # >>> [{'id': 1, 'name': 'Updated name'}, {'id': 2, 'name': 'Test 2'}]
    print(repr(await Event.first()))
    # >>> <Event: 1>
    print(repr(await Event.last()))
    # >>> <Event: 2>


def main() -> None:
    from tortoise import run_async
    from tortoise.contrib.test import init_memory_sqlite

    def run_in_memory_sqlite(func) -> None:
        f = init_memory_sqlite(func)
        run_async(f())

    run_in_memory_sqlite(run)


if __name__ == "__main__":
    main()
