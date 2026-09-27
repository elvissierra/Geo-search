from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.contrib.auth.models import Group

from django.contrib import admin
from geo_search_api.apps.topics.models import Topic, TopicStage, TopicTag


admin.site.unregister(User)
admin.site.unregister(Group)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    pass


@admin.register(TopicStage)
class TopicStageAdmin(admin.ModelAdmin):
    pass


@admin.register(TopicTag)
class TopicTagAdmin(admin.ModelAdmin):
    pass
