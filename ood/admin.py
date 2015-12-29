from django.contrib import admin

from . import models

admin.site.register(models.OodInstance)
admin.site.register(models.MineCraftServerSettings)
admin.site.register(models.ServerPlayerState)
admin.site.register(models.DropletState)
admin.site.register(models.SimpleServerState)
