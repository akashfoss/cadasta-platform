import pytest

from unittest.mock import patch, call
from django.test import TestCase
from django.test.utils import override_settings
from rest_framework.renderers import JSONRenderer

from ..reindex import (api,
                       create_new_index,
                       index_record_type,
                       get_old_index,
                       switch_alias,
                       run)
from core.util import ID_FIELD_LENGTH
from organization.tests.factories import ProjectFactory
from party.models import Party
from party.serializers import PartySerializer
from party.tests.factories import PartyFactory


class ReindexTest(TestCase):
    @patch('requests.put')
    def test_create_new_index(self, mock_put):
        mock_put.return_value.status_code = 200

        project_slug = 'test_slug'
        new_index = create_new_index(project_slug)

        assert len(new_index) == len(project_slug) + 1 + ID_FIELD_LENGTH
        assert new_index[:len(project_slug)] == project_slug
        mock_put.assert_called_once_with(api + '/' + new_index)

    @override_settings(ES_REINDEX_PAGE_SIZE=10)
    @patch('requests.post')
    def test_index_record_type_with_paging(self, mock_post):
        mock_post.return_value.status_code = 200

        project = ProjectFactory()
        PartyFactory.create_batch(20, project=project)

        index_url = api + '/test_index'
        index_record_type(
            project.slug,
            index_url,
            'party',
            Party,
            PartySerializer,
        )

        parties = Party.objects.all()
        mock_call_args = []
        for i in range(0, 20, 10):
            batch_parties = parties[i:i + 10]
            bulk = ''
            for party in batch_parties:
                # ES Bulk API action line
                bulk += '{"create":{"_id":"' + party.id + '"}}\n'
                # ES Bulk API source line
                bulk += JSONRenderer().render(
                    PartySerializer(party, context={'search': True}).data
                ).decode() + '\n'
            mock_call_args.append(call(index_url + '/party/_bulk', data=bulk))

        mock_post.assert_has_calls(mock_call_args)

    @patch('requests.post')
    def test_index_record_type_empty(self, mock_post):
        index_record_type(
            'test_slug',
            api + '/test_index',
            'party',
            Party,
            PartySerializer,
        )

        mock_post.assert_not_called()

    @patch('requests.get')
    def test_get_old_index_existing(self, mock_get):
        mock_get.return_value.json.return_value = {'index': []}

        project_slug = 'test_slug'
        old_index = get_old_index(project_slug)

        assert old_index == 'index'
        mock_get.assert_called_once_with(api + '/_alias/' + project_slug)

    @patch('requests.get')
    def test_get_old_index_does_not_exist(self, mock_get):
        mock_get.return_value.json.return_value = {}

        project_slug = 'test_slug'
        old_index = get_old_index(project_slug)

        assert old_index is None
        mock_get.assert_called_once_with(api + '/_alias/' + project_slug)

    @patch('requests.get')
    def test_get_old_index_invalid(self, mock_get):
        mock_get.return_value.json.return_value = {'index1': [], 'index2': []}

        project_slug = 'test_slug'
        with pytest.raises(AssertionError):
            get_old_index(project_slug)

        mock_get.assert_called_once_with(api + '/_alias/' + project_slug)

    @patch('requests.delete')
    @patch('requests.post')
    def test_switch_alias_no_old_index(self, mock_post, mock_delete):
        mock_post.return_value.status_code = 200

        alias = 'alias'
        old_index = None
        new_index = 'index-3456'
        switch_alias(alias, old_index, new_index)

        data = (
            '{{"actions": ['
            '{{"add": {{"alias": "{}", "index": "{}"}}}}'
            ']}}'
        ).format(alias, new_index)
        mock_post.assert_called_once_with(api + '/_aliases/', data=data)
        mock_delete.assert_not_called()

    @patch('requests.delete')
    @patch('requests.post')
    def test_switch_alias_with_old_index(self, mock_post, mock_delete):
        mock_post.return_value.status_code = 200
        mock_delete.return_value.status_code = 200

        alias = 'alias'
        old_index = 'index-1234'
        new_index = 'index-3456'
        switch_alias(alias, old_index, new_index)

        data = (
            '{{"actions": ['
            '{{"remove": {{"alias": "{}", "index": "{}"}}}}, '
            '{{"add": {{"alias": "{}", "index": "{}"}}}}'
            ']}}'
        ).format(alias, old_index, alias, new_index)
        mock_post.assert_called_once_with(api + '/_aliases/', data=data)
        mock_delete.assert_called_once_with(api + '/' + old_index)

    @patch('requests.delete')
    @patch('requests.put')
    @patch('requests.post')
    @patch('requests.get')
    @patch('search.reindex.random_id')
    def test_run(self, mock_rid, mock_get, mock_post, mock_put, mock_delete):
        mock_rid.return_value = '123456789012345678901234'
        mock_get.return_value.json.return_value = {}
        mock_post.return_value.status_code = 200
        mock_put.return_value.status_code = 200

        project = ProjectFactory()
        run(project.slug)

        new_index = project.slug + '-' + mock_rid.return_value
        data = (
            '{{"actions": ['
            '{{"add": {{"alias": "{}", "index": "{}"}}}}'
            ']}}'
        ).format(project.slug, new_index)
        mock_put.assert_called_once_with(api + '/' + new_index)
        mock_get.assert_called_once_with(api + '/_alias/' + project.slug)
        mock_post.assert_called_once_with(api + '/_aliases/', data=data)
        mock_delete.assert_not_called()
