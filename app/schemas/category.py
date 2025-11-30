from pydantic import BaseModel, ConfigDict, Field, field_validator

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=30)

    @field_validator('name')
    def validate_name(cls, v: str):
        if any(char.isdigit() for char in v):
            raise ValueError('Название категории не должно содержать цифр')
        return v.strip().title()

class CategoryCreate(CategoryBase):
    pass

class CategoryRead(CategoryBase):
    id: int
    model_config = ConfigDict(from_attributes=True)