from django.db import models

class Lectura(models.Model):
    id = models.AutoField(primary_key=True)
    estacion = models.CharField(max_length=50, db_index=True) 
    sensor = models.CharField(max_length=50, null=True, blank=True)
    valor = models.FloatField(null=True, blank=True)
    fecha = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = 'lecturas'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['estacion', '-fecha']),
        ]

    def __str__(self):  
        return f"{self.estacion} - {self.sensor} - {self.valor}"
