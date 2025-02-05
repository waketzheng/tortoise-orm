from decimal import Decimal
from typing import ClassVar

from tests import testmodels
from tortoise import Model
from tortoise.contrib import test
from tortoise.exceptions import ValidationError
from tortoise.expressions import F


class TestIntNum(test.TestCase):
    model: ClassVar[type[Model]] = testmodels.IntFields

    async def test_empty(self):
        with self.assertRaises(ValidationError):
            await self.model.create()

    async def test_value_range(self):
        try:
            # tests.testmodels.IntFields/BigIntFields
            field = self.model._meta.fields_map["intnum"]
        except KeyError:
            # tests.testmodels.SmallIntFields
            field = self.model._meta.fields_map["smallintnum"]
        min_, max_ = field.constraints["ge"], field.constraints["le"]
        with self.assertRaises(ValidationError):
            await self.model.create(intnum=min_ - 1)
        with self.assertRaises(ValidationError):
            await self.model.create(intnum=max_ + 1)
        with self.assertRaises(ValidationError):
            await self.model.create(intnum=max_ + 1.1)
        with self.assertRaises(ValidationError):
            await self.model.create(intnum=Decimal(max_ + 1.1))


class TestIntFields(test.TestCase):
    async def test_create(self):
        obj0 = await testmodels.IntFields.create(intnum=2147483647)
        obj = await testmodels.IntFields.get(id=obj0.id)
        self.assertEqual(obj.intnum, 2147483647)
        self.assertEqual(obj.intnum_null, None)

        obj2 = await testmodels.IntFields.get(id=obj.id)
        self.assertEqual(obj, obj2)

        await obj.delete()
        obj = await testmodels.IntFields.filter(id=obj0.id).first()
        self.assertEqual(obj, None)

    async def test_update(self):
        obj0 = await testmodels.IntFields.create(intnum=2147483647)
        await testmodels.IntFields.filter(id=obj0.id).update(intnum=2147483646)
        obj = await testmodels.IntFields.get(id=obj0.id)
        self.assertEqual(obj.intnum, 2147483646)
        self.assertEqual(obj.intnum_null, None)

    async def test_min(self):
        obj0 = await testmodels.IntFields.create(intnum=-2147483648)
        obj = await testmodels.IntFields.get(id=obj0.id)
        self.assertEqual(obj.intnum, -2147483648)
        self.assertEqual(obj.intnum_null, None)

        obj2 = await testmodels.IntFields.get(id=obj.id)
        self.assertEqual(obj, obj2)

    async def test_cast(self):
        obj0 = await testmodels.IntFields.create(intnum="3")
        obj = await testmodels.IntFields.get(id=obj0.id)
        self.assertEqual(obj.intnum, 3)

    async def test_values(self):
        obj0 = await testmodels.IntFields.create(intnum=1)
        values = await testmodels.IntFields.get(id=obj0.id).values("intnum")
        self.assertEqual(values["intnum"], 1)

    async def test_values_list(self):
        obj0 = await testmodels.IntFields.create(intnum=1)
        values = await testmodels.IntFields.get(id=obj0.id).values_list("intnum", flat=True)
        self.assertEqual(values, 1)

    async def test_f_expression(self):
        obj0 = await testmodels.IntFields.create(intnum=1)
        await obj0.filter(id=obj0.id).update(intnum=F("intnum") + 1)
        obj1 = await testmodels.IntFields.get(id=obj0.id)
        self.assertEqual(obj1.intnum, 2)


class TestSmallIntFields(TestIntNum):
    model = testmodels.SmallIntFields

    async def test_create(self):
        obj0 = await testmodels.SmallIntFields.create(smallintnum=32767)
        obj = await testmodels.SmallIntFields.get(id=obj0.id)
        self.assertEqual(obj.smallintnum, 32767)
        self.assertEqual(obj.smallintnum_null, None)
        await obj.save()
        obj2 = await testmodels.SmallIntFields.get(id=obj.id)
        self.assertEqual(obj, obj2)

    async def test_min(self):
        obj0 = await testmodels.SmallIntFields.create(smallintnum=-32768)
        obj = await testmodels.SmallIntFields.get(id=obj0.id)
        self.assertEqual(obj.smallintnum, -32768)
        self.assertEqual(obj.smallintnum_null, None)
        await obj.save()
        obj2 = await testmodels.SmallIntFields.get(id=obj.id)
        self.assertEqual(obj, obj2)

    async def test_values(self):
        obj0 = await testmodels.SmallIntFields.create(smallintnum=2)
        values = await testmodels.SmallIntFields.get(id=obj0.id).values("smallintnum")
        self.assertEqual(values["smallintnum"], 2)

    async def test_values_list(self):
        obj0 = await testmodels.SmallIntFields.create(smallintnum=2)
        values = await testmodels.SmallIntFields.get(id=obj0.id).values_list(
            "smallintnum", flat=True
        )
        self.assertEqual(values, 2)

    async def test_f_expression(self):
        obj0 = await testmodels.SmallIntFields.create(smallintnum=1)
        await obj0.filter(id=obj0.id).update(smallintnum=F("smallintnum") + 1)
        obj1 = await testmodels.SmallIntFields.get(id=obj0.id)
        self.assertEqual(obj1.smallintnum, 2)


class TestBigIntFields(TestIntNum):
    model = testmodels.BigIntFields

    async def test_create(self):
        obj0 = await testmodels.BigIntFields.create(intnum=9223372036854775807)
        obj = await testmodels.BigIntFields.get(id=obj0.id)
        self.assertEqual(obj.intnum, 9223372036854775807)
        self.assertEqual(obj.intnum_null, None)
        await obj.save()
        obj2 = await testmodels.BigIntFields.get(id=obj.id)
        self.assertEqual(obj, obj2)

    async def test_min(self):
        obj0 = await testmodels.BigIntFields.create(intnum=-9223372036854775808)
        obj = await testmodels.BigIntFields.get(id=obj0.id)
        self.assertEqual(obj.intnum, -9223372036854775808)
        self.assertEqual(obj.intnum_null, None)
        await obj.save()
        obj2 = await testmodels.BigIntFields.get(id=obj.id)
        self.assertEqual(obj, obj2)

    async def test_cast(self):
        obj0 = await testmodels.BigIntFields.create(intnum="3")
        obj = await testmodels.BigIntFields.get(id=obj0.id)
        self.assertEqual(obj.intnum, 3)

    async def test_values(self):
        obj0 = await testmodels.BigIntFields.create(intnum=1)
        values = await testmodels.BigIntFields.get(id=obj0.id).values("intnum")
        self.assertEqual(values["intnum"], 1)

    async def test_values_list(self):
        obj0 = await testmodels.BigIntFields.create(intnum=1)
        values = await testmodels.BigIntFields.get(id=obj0.id).values_list("intnum", flat=True)
        self.assertEqual(values, 1)

    async def test_f_expression(self):
        obj0 = await testmodels.BigIntFields.create(intnum=1)
        await obj0.filter(id=obj0.id).update(intnum=F("intnum") + 1)
        obj1 = await testmodels.BigIntFields.get(id=obj0.id)
        self.assertEqual(obj1.intnum, 2)
