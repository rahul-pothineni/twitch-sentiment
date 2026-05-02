from django.contrib import admin

from db.models import Session, Streamer, Message


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ("id", "start_time", "end_time")
    list_filter = ("start_time", "end_time")
    readonly_fields = ("id",)
    ordering = ("-start_time",)


@admin.register(Streamer)
class StreamerAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "session")
    list_filter = ("session",)
    search_fields = ("username",)
    ordering = ("session", "username")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "streamer", "sent_at", "sentiment", "content_preview")
    list_filter = ("sent_at", "streamer")
    search_fields = ("content",)
    readonly_fields = ("sent_at",)
    ordering = ("-sent_at",)

    @admin.display(description="Content")
    def content_preview(self, obj: Message) -> str:
        text = (obj.content or "")[:80]
        return f"{text}…" if len(obj.content or "") > 80 else text