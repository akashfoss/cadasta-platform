import requests

from django.conf import settings
from rest_framework.renderers import JSONRenderer

from spatial.models import SpatialUnit
from spatial.serializers import SpatialUnitSerializer
from party.models import Party, TenureRelationship
from party.serializers import PartySerializer
from party.serializers import TenureRelationshipWriteSerializer
from resources.models import Resource
from resources.serializers import ResourceSerializer


def run(project_slug, verbose=True):

    assert settings.ES_SCHEME in ['http', 'https']
    api = (
        settings.ES_SCHEME + '://' + settings.ES_HOST + ':' + settings.ES_PORT)
    page_size = settings.ES_REINDEX_PAGE_SIZE

    # TODO: Pause batch processing by calling SQS

    # Create project index
    # TODO: Figure out how to do aliasing
    index_url = api + '/' + project_slug
    r = requests.put(index_url)
    assert r.status_code == 200

    # Index project's records and resources
    for record_types in [
        ('location', SpatialUnit, SpatialUnitSerializer),
        ('party', Party, PartySerializer),
        ('tenure_rel', TenureRelationship, TenureRelationshipWriteSerializer),
        ('resource', Resource, ResourceSerializer),
    ]:
        es_type = record_types[0]
        model = record_types[1]
        serializer = record_types[2]

        records = model.objects.filter(project__slug=project_slug)
        if records:
            for i in range(0, len(records), page_size):
                batch_records = records[i:i + page_size]
                bulk = ''
                for record in batch_records:
                    # ES Bulk API action line
                    bulk += '{"create":{"_id":"' + record.id + '"}}\n'
                    # ES Bulk API source line
                    bulk += JSONRenderer().render(
                        serializer(record, context={'search': True}).data
                    ).decode() + '\n'
                print(bulk)
                r = requests.post(
                    index_url + '/' + es_type + '/_bulk', data=bulk)

    # TODO: Resume batch processing by calling SQS
