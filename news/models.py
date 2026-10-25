from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce


class Author(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="author_profile",
    )
    rating = models.IntegerField(default=0)

    def update_rating(self):
        post_rating = (
            Post.objects.filter(author=self).aggregate(total=Sum("rating"))["total"]
            or 0
        )
        comment_rating_by_author = (
            Comment.objects.filter(user=self.user).aggregate(total=Sum("rating"))["total"]
            or 0
        )
        comment_rating_on_author_posts = (
            Comment.objects.filter(post__author=self).aggregate(total=Sum("rating"))["total"]
            or 0
        )

        self.rating = (
            post_rating * 3
            + comment_rating_by_author
            + comment_rating_on_author_posts
        )
        self.save(update_fields=["rating"])

    def __str__(self):
        return self.user.username


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    ARTICLE = "article"
    NEWS = "news"

    POST_TYPES = [
        (ARTICLE, "Статья"),
        (NEWS, "Новость"),
    ]

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    post_type = models.CharField(max_length=10, choices=POST_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    categories = models.ManyToManyField(
        Category,
        through="PostCategory",
        related_name="posts",
    )
    title = models.CharField(max_length=255)
    text = models.TextField()
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save(update_fields=["rating"])

    def dislike(self):
        self.rating -= 1
        self.save(update_fields=["rating"])

    def preview(self):
        return self.text[:124] + "..."

    def __str__(self):
        return self.title


class PostCategory(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="post_categories",
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="post_categories",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["post", "category"],
                name="unique_post_category",
            )
        ]

    def __str__(self):
        return f"{self.post} — {self.category}"


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(default=0)

    def like(self):
        self.rating += 1
        self.save(update_fields=["rating"])

    def dislike(self):
        self.rating -= 1
        self.save(update_fields=["rating"])

    def __str__(self):
        return f"Комментарий пользователя {self.user}"