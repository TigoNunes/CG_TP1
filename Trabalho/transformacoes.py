from typing import Iterable, Tuple

# Importamos as entidades para poder aplicar transformações
from entities import Ponto, Reta, Circunferencia, Poligono


class Transformacao:
    """Classe base para as transformações geométricas."""

    def __init__(self, entidades: Iterable):
        self.entidades = list(entidades)

    def aplicar(self):
        """Aplica a transformação nas entidades.

        Cada subclasse deve implementar este método.
        """
        raise NotImplementedError("Subclasses devem implementar o método aplicar().")


class Translacao(Transformacao):
    """Aplica translação (deslocamento) em entidades."""

    def __init__(self, entidades: Iterable, dx: float, dy: float):
        super().__init__(entidades)
        self.dx = dx
        self.dy = dy

    def aplicar(self):
        for entidade in self.entidades:
            # As entidades de entities.py implementam translate(dx, dy)
            entidade.translate(self.dx, self.dy)


class Escala(Transformacao):
    """Aplica escala uniforme nas entidades em relação a um pivô."""

    def __init__(self, entidades: Iterable, fator: float, pivot: Tuple[float, float] = (0, 0)):
        super().__init__(entidades)
        self.fator = fator
        self.pivot = pivot

    def aplicar(self):
        for entidade in self.entidades:
            # As entidades de entities.py implementam scale(fator, pivot)
            entidade.scale(self.fator, self.pivot)


class Rotacao(Transformacao):
    """Aplica rotação (em graus) nas entidades em torno de um pivô."""

    def __init__(self, entidades: Iterable, angulo_graus: float, pivot: Tuple[float, float] = (0, 0)):
        super().__init__(entidades)
        self.angulo_graus = angulo_graus
        self.pivot = pivot

    def aplicar(self):
        for entidade in self.entidades:
            # As entidades de entities.py implementam rotate(angle, pivot)
            entidade.rotate(self.angulo_graus, self.pivot)