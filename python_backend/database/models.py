from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    discord_id = Column(String, unique=True, nullable=False)
    wallet_address = Column(String, nullable=True)
    balance = Column(Float, default=0.0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    last_1v1_battle_at = Column(DateTime, nullable=True)
    # Add other stats as needed

class Tournament(Base):
    __tablename__ = 'tournaments'
    id = Column(Integer, primary_key=True)
    status = Column(String, default="pending") # pending, active, completed
    bracket_size = Column(Integer, default=8)
    current_round = Column(Integer, default=1)
    winner_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    
    matches = relationship("Match", back_populates="tournament")

class Match(Base):
    __tablename__ = 'matches'
    id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey('tournaments.id'))
    player1_id = Column(Integer, ForeignKey('players.id'))
    player2_id = Column(Integer, ForeignKey('players.id'))
    winner_id = Column(Integer, ForeignKey('players.id'), nullable=True)
    round_number = Column(Integer)
    
    tournament = relationship("Tournament", back_populates="matches")
    player1 = relationship("Player", foreign_keys=[player1_id])
    player2 = relationship("Player", foreign_keys=[player2_id])
    winner = relationship("Player", foreign_keys=[winner_id])

class Bet(Base):
    __tablename__ = 'bets'
    id = Column(Integer, primary_key=True)
    match_id = Column(Integer, ForeignKey('matches.id'))
    player_id = Column(Integer, ForeignKey('players.id')) # The user placing the bet
    amount = Column(Float, nullable=False)
    predicted_winner_id = Column(Integer, ForeignKey('players.id'))
    
    match = relationship("Match")
    player = relationship("Player", foreign_keys=[player_id])

class Tenant(Base):
    __tablename__ = 'tenants'
    id = Column(Integer, primary_key=True)
    guild_id = Column(String, unique=True, nullable=False)
    theme = Column(String, default="default")
    token_symbol = Column(String, default="SOL")
