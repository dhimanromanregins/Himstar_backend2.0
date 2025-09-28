from django.db import models

# Create your models here.



class Stage_Levels(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name}"



class Stage(models.Model):
    name = models.ForeignKey(Stage_Levels, on_delete=models.CASCADE, related_name="levelsmkl")
    likes_required = models.PositiveIntegerField()
    award = models.URLField(blank=True, null=True)
    border_design = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.likes_required} Likes Required"

class Level(models.Model):
    current_stage = models.ForeignKey(Stage, on_delete=models.CASCADE, related_name="levels")
    likes = models.BigIntegerField(default=0)

    def __str__(self):
        return f"{self.popularity.name} - {self.current_stage.name} Stage"