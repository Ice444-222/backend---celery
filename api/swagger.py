from .serializers import UserBasicSerializer


def list_swagger():
    operation_id="Get User List",
    operation_description="Retrieve a list of users.",
    responses={
        200: UserBasicSerializer(many=True),
        403: "Permission Denied"
    },
    tags=['Users'],
    