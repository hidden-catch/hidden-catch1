import React from 'react';
import './Header.css';

function Header({ onNavigate, currentPage }) {
  const handleLogin = () => {
    // TODO: 로그인 기능 구현
    console.log('로그인 클릭');
  };

  const handleSignup = () => {
    // TODO: 가입 기능 구현
    console.log('가입 클릭');
  };

  const handleRank = () => {
    // TODO: 랭크 기능 구현
    console.log('랭크 클릭');
  };

  const handleGoHome = () => {
    if (!onNavigate) return;

    // 게임 페이지에서 홈으로 이동할 때 확인
    if (currentPage === 'game') {
      const gameRoomId = localStorage.getItem('currentGameRoomId');
      
      // 게임이 진행 중인 경우에만 확인
      if (gameRoomId) {
        const confirmed = window.confirm(
          '게임을 종료하시겠습니까?\n진행 중인 게임 데이터가 저장되지 않습니다.'
        );
        
        if (!confirmed) {
          return;
        }
      }
    }
    
    onNavigate('home');
  };

  return (
    <header className="header">
      <div className="header-title" onClick={handleGoHome}>
        <h1>
          Hidden Catc<span className="magnifying-glass-wrapper">h</span>
        </h1>
      </div>
      <nav className="header-nav">
        <button onClick={handleLogin} className="nav-button">로그인</button>
        <button onClick={handleSignup} className="nav-button">가입</button>
        <button onClick={handleRank} className="nav-button">랭크</button>
      </nav>
    </header>
  );
}

export default Header;
