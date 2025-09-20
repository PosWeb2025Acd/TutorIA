function checkToken() {
      const token = localStorage.getItem('authToken');
      const storedUserData = localStorage.getItem('userData');

      if (!token || !storedUserData) {
        // Redirecionar para login se não houver token ou dados do usuário
        window.location.href = '/';
        return null;
      }

      return JSON.parse(storedUserData);
}

export default checkToken;
