import { Navigate, Outlet } from "react-router-dom";

function AdminRouter() {
    const userToken = localStorage.getItem('authToken');
    const userIsLogged = userToken !== null && userToken !== undefined && userToken !== ''
    if (userIsLogged) {
        const userData = JSON.parse(localStorage.getItem('userData'));
        if (userData && userData.admin) {
            return <Outlet />
        }
        return <Navigate to="/tutor-ia/chat" />
    }

    return <Navigate to="/tutor-ia/chat" />
}

export default AdminRouter
