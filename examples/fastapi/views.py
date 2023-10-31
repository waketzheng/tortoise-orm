from typing import List

from fastapi import APIRouter, Path
from models import User_Pydantic, UserIn_Pydantic, Users
from pydantic import BaseModel
from starlette.exceptions import HTTPException

try:
    from typing import Annotated
except ModuleNotFoundError:
    from typing_extensions import Annotated


class Status(BaseModel):
    message: str


app = APIRouter()
UserId = Annotated[int, Path(gt=0)]
UserInData = Annotated[UserIn_Pydantic, "User data without id"]


@app.get("/users", response_model=List[User_Pydantic])
async def get_users():
    return await User_Pydantic.from_queryset(Users.all())


@app.post("/users", response_model=User_Pydantic)
async def create_user(user: UserInData):
    user_obj = await Users.create(**user.model_dump(exclude_unset=True))
    return await User_Pydantic.from_tortoise_orm(user_obj)


@app.get("/user/{user_id}", response_model=User_Pydantic)
async def get_user(user_id: UserId):
    return await User_Pydantic.from_queryset_single(Users.get(id=user_id))


@app.put("/user/{user_id}", response_model=User_Pydantic)
async def update_user(user_id: UserId, user: UserInData):
    await Users.filter(id=user_id).update(**user.model_dump(exclude_unset=True))
    return await User_Pydantic.from_queryset_single(Users.get(id=user_id))


@app.delete("/user/{user_id}", response_model=Status)
async def delete_user(user_id: UserId):
    deleted_count = await Users.filter(id=user_id).delete()
    if not deleted_count:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return Status(message=f"Deleted user {user_id}")
