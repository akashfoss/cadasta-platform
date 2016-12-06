import boto3
import json
from django.dispatch import receiver
from django.db import models

from party.queue_name import return_queue_name
from party import serializers
from spatial.serializers import SpatialUnitSerializer
from resources.serializers import ResourceSerializer

sqs = boto3.resource('sqs')
# This needs to be updated once we have the queue variable in production.txt
queue = sqs.get_queue_by_name(QueueName=return_queue_name())


@receiver(models.signals.pre_delete)
def update_search_index(sender, instance, **kwargs):
    sender = sender.__base__ if sender._deferred else sender
    serializer = None

    if sender.__name__ == 'Party':
        serializer = serializers.PartySerializer

    if sender.__name__ == 'TenureRelationship':
        serializer = serializers.TenureRelationshipWriteSerializer

    if sender.__name__ == 'SpatialUnit':
        serializer = SpatialUnitSerializer

    if sender.__name__ == 'Resource':
        serializer = ResourceSerializer

    if serializer:
        data = serializer(context={'search': True}).to_representation(instance)
        json_data = json.dumps(data)
        queue.send_message(
            MessageGroupId='searchIndexUpdate',
            MessageBody=json_data,
        )

models.signals.post_save.connect(update_search_index)
