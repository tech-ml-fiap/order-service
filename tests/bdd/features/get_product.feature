Feature: Obter produto

  Scenario: Produto encontrado
    Given um produto "68802" existe no catálogo
    When eu chamar get_product com "68802"
    Then devo receber os dados do produto

  Scenario: Produto não existe
    Given nenhum produto "99999" existe no catálogo
    When eu chamar get_product com "99999"
    Then deve lançar erro "Produto 99999 não encontrado"
