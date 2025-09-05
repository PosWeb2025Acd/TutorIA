import { Navigate, Outlet } from "react-router-dom";

function ProtectedRoute() {
    const userToken = localStorage.getItem('authToken');
    const userIsLogged = userToken !== null && userToken !== undefined && userToken !== ''

    return userIsLogged ? <Outlet /> : <Navigate to="/" />
}

export default ProtectedRoute
