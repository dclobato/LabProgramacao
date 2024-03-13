import sqlalchemy as sa

from .auth import User
from .pedido import Endereco
from .produto import Produto

User.lista_de_enderecos = sa.orm.relationship("Endereco",
                                              back_populates="usuario",
                                              lazy="select",
                                              cascade="all, delete-orphan")

User.lista_de_pedidos = sa.orm.relationship("Pedido",
                                            back_populates="usuario",
                                            lazy="select",
                                            cascade="all, delete-orphan")

Endereco.lista_de_pedidos = sa.orm.relationship("Pedido",
                                                back_populates="endereco",
                                                lazy="select",
                                                cascade="all, delete-orphan")

Produto.lista_de_pedidos = sa.orm.relationship("ItemPedido",
                                               back_populates="produto",
                                               lazy="select",
                                               cascade="all, delete-orphan")
