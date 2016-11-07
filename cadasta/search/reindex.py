import requests
import json

from django.conf import settings
from rest_framework.renderers import JSONRenderer

from core.util import random_id
from spatial.models import SpatialUnit
from spatial.serializers import SpatialUnitSerializer
from party.models import Party, TenureRelationship
from party.serializers import PartySerializer
from party.serializers import TenureRelationshipWriteSerializer
from resources.models import Resource
from resources.serializers import ResourceSerializer


api = settings.ES_SCHEME + '://' + settings.ES_HOST + ':' + settings.ES_PORT


def create_new_index(project_slug):
    """This routine creates a new project index and returns it."""

    new_index = project_slug + '-' + random_id()
    r = requests.put(api + '/' + new_index)
    assert r.status_code == 200
    return new_index


def index_record_type(project_slug, index_url, es_type, model, serializer):
    """This routine indexes the project's records of the specified record type
    (ES type label, Django model, and DRF serializer) using the ES Bulk API."""

    page_size = settings.ES_REINDEX_PAGE_SIZE
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
            r = requests.post(
                index_url + '/' + es_type + '/_bulk', data=bulk)
            assert r.status_code == 200


def get_old_index(project_slug):
    """This routine queries the ES cluster for the actual index name for the
    specified project and returns the name."""

    r = requests.get(api + '/_alias/' + project_slug)
    indices = list(r.json().keys())
    assert len(indices) <= 1
    if len(indices) == 1:
        return indices[0]
    else:
        return None


def switch_alias(alias, old_index, new_index):
    """This routine switches the alias to point to the new index and deletes
    the old index if it exists."""

    body = {'actions': [{'add': {'index': new_index, 'alias': alias}}]}
    if old_index:
        body['actions'].insert(
            0, {'remove': {'index': old_index, 'alias': alias}})
    json_string = json.dumps(body, sort_keys=True)
    r = requests.post(api + '/_aliases/', data=json_string)
    assert r.status_code == 200

    if old_index:
        r = requests.delete(api + '/' + old_index)
        assert r.status_code == 200


def run(project_slug, verbose=True):

    assert settings.ES_SCHEME in ['http', 'https']

    # TODO: Pause batch processing by calling SQS

    # Create project index with random suffix
    new_index = create_new_index(project_slug)

    # Index project's records and resources
    for record_types in [
        ('location', SpatialUnit, SpatialUnitSerializer),
        ('party', Party, PartySerializer),
        ('tenure_rel', TenureRelationship, TenureRelationshipWriteSerializer),
        ('resource', Resource, ResourceSerializer),
    ]:
        index_record_type(
            project_slug,
            api + '/' + new_index,
            record_types[0],
            record_types[1],
            record_types[2],
        )

    # Switch alias to point to the new index
    # and delete the previous index if any
    old_index = get_old_index(project_slug)
    switch_alias(project_slug, old_index, new_index)

    # TODO: Resume batch processing by calling SQS
