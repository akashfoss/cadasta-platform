import requests

from django.conf import settings
from rest_framework.renderers import JSONRenderer

from organization.models import Project
from spatial.models import SpatialUnit
from spatial.serializers import SpatialUnitSerializer
# from party.models import Party, TenureRelationship
# from party.serializers import PartySerializer
# from party.serializers import TenureRelationshipWriteSerializer


def run(verbose=True):

    api = 'http://' + settings.ES_HOST + ':' + settings.ES_PORT

    for prj in Project.objects.all():

        # Delete then create project index
        index_url = api + '/' + prj.slug
        r = requests.delete(index_url)
        r = requests.put(index_url)
        assert r.status_code == 200

        # Index each location
        locs = SpatialUnit.objects.filter(project=prj)[:10]
        if locs:
            for loc in locs:
                doc = JSONRenderer().render(SpatialUnitSerializer(loc).data)
                r = requests.post(index_url + '/location/', data=doc)
