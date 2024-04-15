from django.contrib import admin

from .models import Title, Genres, Categories


class TitlesAdmin(admin.ModelAdmin):
    list_display = ('pk', 'name', 'year', 'category')
    list_display_links = ('pk', 'name',)
    list_filter = ('name',)
    search_fields = ('name',)
    empty_value_display = '-пусто-'

    list_editable = ('category',)


admin.site.register(Title, TitlesAdmin)
admin.site.register(Genres)
admin.site.register(Categories)
