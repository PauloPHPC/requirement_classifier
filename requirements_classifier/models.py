from django.db import models

# Create your models here.

class Documents(models.Model):
    document_name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.document_name
    

class Requirements(models.Model):
    text = models.TextField(blank=False, null=False)
    classification_ai = models.CharField(max_length=20)
    confidence_ai = models.FloatField()
    classification_user = models.CharField(max_length=20)
    original_text = models.TextField()
    match_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    page = models.IntegerField()

    project = models.ForeignKey(Documents, on_delete=models.CASCADE, related_name="requirements")

    def __str__(self):
        return f"{self.text[:50]}... ({self.classification_ai})"