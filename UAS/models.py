from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class Coffe(Base):
    __tablename__ = 'CoffeeShop'
    id: Mapped[str] = mapped_column(primary_key=True)
    namatoko: Mapped[str] = mapped_column()
    rasa: Mapped[int] = mapped_column()
    harga: Mapped[int] = mapped_column()
    pelayanan: Mapped[int] = mapped_column()
    suasana: Mapped[int] = mapped_column()
    jarak: Mapped[int] = mapped_column()  
    
    def __repr__(self) -> str:
        return f"Coffe(id={self.id!r}, harga={self.harga!r})"
