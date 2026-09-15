from rest_framework.response import Response

from families.services import get_user_family


class EnvelopeMixin:
    success_messages = {
        "create": "Created successfully.",
        "update": "Updated successfully.",
        "destroy": "Deleted successfully.",
        "list": "",
        "retrieve": "",
    }

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if not isinstance(response, Response):
            return response
        if isinstance(response.data, dict) and "success" in response.data:
            return response
        if response.status_code == 204:
            response.status_code = 200
            response.data = {
                "success": True,
                "message": self.success_messages.get("destroy", "Deleted successfully."),
                "data": None,
            }
            return response
        action = getattr(self, "action", "")
        response.data = {
            "success": response.status_code < 400,
            "message": self.success_messages.get(action, ""),
            "data": response.data,
        }
        return response


class FamilyContextMixin:
    family = None
    membership = None

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.user and request.user.is_authenticated:
            self.family, self.membership = get_user_family(request.user)

    def get_family(self):
        if self.family is None:
            self.family, self.membership = get_user_family(self.request.user)
        return self.family
