"""Party serializer test cases."""

from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from jsonattrs.models import Attribute, AttributeType, Schema

from core.tests.utils.cases import UserTestCase
from organization.tests.factories import ProjectFactory
from party import serializers

from .factories import PartyFactory, TenureRelationshipFactory


class PartySerializerTest(UserTestCase, TestCase):
    def test_serialize_party(self):
        party = PartyFactory.create()
        serializer = serializers.PartySerializer(party)
        serialized = serializer.data

        assert serialized['id'] == party.id
        assert serialized['name'] == party.name
        assert serialized['type'] == party.type
        assert 'attributes' in serialized

    def test_create_party(self):
        project = ProjectFactory.create(name='Test Project')

        party_data = {'name': 'Tea Party'}
        serializer = serializers.PartySerializer(
            data=party_data,
            context={'project': project}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        party_instance = serializer.instance
        assert party_instance.name == 'Tea Party'

    def test_serialize_party_search_mode(self):
        project = ProjectFactory.create(current_questionnaire='a1')
        content_type = ContentType.objects.get(
            app_label='party', model='party')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, 'a1'))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='fname',
            long_name='Test field',
            attr_type=attr_type,
            index=0,
            required=False,
            omit=False
        )
        party = PartyFactory.create(
            project=project, attributes={'fname': 'Test'})
        serializer = serializers.PartySerializer(
            party, context={'search': True})
        serialized = serializer.data

        assert 'id' not in serialized
        assert 'attributes' not in serialized
        assert serialized['name'] == party.name
        assert serialized['type'] == party.type
        assert serialized['fname'] == party.attributes['fname']


class TenureRelationshipSerializerTest(UserTestCase, TestCase):
    def test_serialize_tenure_rel_search_mode(self):
        project = ProjectFactory.create(current_questionnaire='a1')
        content_type = ContentType.objects.get(
            app_label='party', model='tenurerelationship')
        schema = Schema.objects.create(
            content_type=content_type,
            selectors=(project.organization.id, project.id, 'a1'))
        attr_type = AttributeType.objects.get(name='text')
        Attribute.objects.create(
            schema=schema,
            name='fname',
            long_name='Test field',
            attr_type=attr_type,
            index=0,
            required=False,
            omit=False
        )
        rel = TenureRelationshipFactory.create(
            project=project, attributes={'fname': 'Test'})
        serializer = serializers.TenureRelationshipWriteSerializer(
            rel, context={'search': True})
        serialized = serializer.data

        assert 'id' not in serialized
        assert 'attributes' not in serialized
        assert serialized['party'] == rel.party.id
        assert serialized['spatial_unit'] == rel.spatial_unit.id
        assert serialized['tenure_type'] == rel.tenure_type.id
        assert serialized['fname'] == rel.attributes['fname']
