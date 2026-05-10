"""API REST endpoints — Django Ninja."""
from ninja import Router, Schema
from django.shortcuts import get_object_or_404

from ..models import ExampleModel

router = Router(tags=["Mi Módulo"])


class ExampleIn(Schema):
    """Schema para crear ExampleModel."""
    name: str
    description: str = ""
    amount: float


class ExampleOut(Schema):
    """Schema de respuesta."""
    id: int
    name: str
    amount: float
    created_at: str


@router.get("/", response=list[ExampleOut])
def list_examples(request):
    """Lista todos los objetos de la company activa."""
    company = request.active_company
    qs = ExampleModel.objects.filter(company=company)
    return [
        {
            "id": obj.id,
            "name": obj.name,
            "amount": float(obj.amount),
            "created_at": obj.created_at.isoformat(),
        }
        for obj in qs
    ]


@router.post("/")
def create_example(request, data: ExampleIn):
    """Crea un nuevo Example."""
    company = request.active_company
    obj = ExampleModel.objects.create(
        company=company,
        name=data.name,
        description=data.description,
        amount=data.amount,
        created_by=request.user,
    )
    return {"id": obj.id, "name": obj.name}
