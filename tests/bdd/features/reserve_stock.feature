Feature: Reservar estoque

  Scenario: Reserva bem-sucedida
    Given o produto "ABC" possui estoque
    When eu reservar 2 unidades de "ABC"
    Then a reserva deve acontecer sem erros

  Scenario: Sem estoque suficiente
    Given o produto "XYZ" não possui estoque suficiente
    When eu reservar 5 unidades de "XYZ"
    Then deve lançar erro "Estoque insuficiente para XYZ"
