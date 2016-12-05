# import boto3
from django.contrib import messages
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
# from django.dispatch import receiver
from django.utils.translation import gettext as _
from django.db import models

from tutelary import mixins
# from party.queue_name import return_queue_name
# from party.models import Party, TenureRelationship
# from spatial.models import SpatialUnit
# from party.serializers import PartySerializer


class PermissionRequiredMixin(mixins.PermissionRequiredMixin):
    def handle_no_permission(self):
        msg = super().handle_no_permission()
        messages.add_message(self.request, messages.WARNING,
                             msg[0] if len(msg) > 0 and len(msg[0]) > 0
                             else _("You don't have permission "
                                    "for this action."))

        referer = self.request.META.get('HTTP_REFERER')
        redirect_url = self.request.META.get('HTTP_REFERER', '/')

        if (referer and '/account/login/' in referer and
                not self.request.user.is_anonymous()):

            if 'organization' in self.kwargs and 'project' in self.kwargs:
                redirect_url = reverse(
                    'organization:project-dashboard',
                    kwargs={'organization': self.kwargs['organization'],
                            'project': self.kwargs['project']}
                )
                if redirect_url == self.request.get_full_path():
                    redirect_url = reverse(
                        'organization:dashboard',
                        kwargs={'slug': self.kwargs['organization']}
                    )

            elif 'slug' in self.kwargs:
                redirect_url = reverse(
                    'organization:dashboard',
                    kwargs={'slug': self.kwargs['slug']}
                )
                if redirect_url == self.request.get_full_path():
                    redirect_url = reverse('core:dashboard')

        return redirect(redirect_url)


class LoginPermissionRequiredMixin(PermissionRequiredMixin,
                                   mixins.LoginPermissionRequiredMixin):
    pass


def update_permissions(permission, obj=None):
    def set_permissions(self, request, view=None):
        if (hasattr(self, 'get_organization') and
                self.get_organization().archived):
                    return False
        if (hasattr(self, 'get_project') and self.get_project().archived):
            return False
        if obj and self.get_object().archived:
            return False
        return permission
    return set_permissions


# this should not be hardcoded.
# sqs = boto3.resource('sqs')
# queue = sqs.get_queue_by_name(QueueName=return_queue_name())


# @receiver(models.signals.pre_delete)
# def update_search_index(sender, instance, **kwargs):
#     list_of_models = ('Party', 'TenureRelationship', 'SpatialUnit')
#     # What actually needs to go in the MessageBody?
#     # What should the groupID be?
#     sender = sender.__base__ if sender._deferred else sender
#     project = (instance.project.name if hasattr(instance, 'project')
#                else instance.project_id)
#     print(PartySerializer().to_representation(instance))
#     if sender.__name__ in list_of_models:
#         print('message sent to queue')
#         queue.send_message(
#             MessageGroupId='searchIndexUpdate',
#             MessageBody='{} needs to be updated.'.format(project),
#         )
    # Once merged with eugene's search-reindex
    # PartySerializer().to_representation(party)
    # Returns:
    # OrderedDict([('id', 'drxzdy6x7xau44q9y5nttbjs'),
    # ('name', 'Party #0'), ('type', 'IN'), ('attributes', {})])

# models.signals.post_save.connect(update_search_index, sender=Party)
# models.signals.post_save.connect(
#     update_search_index, sender=TenureRelationship)
