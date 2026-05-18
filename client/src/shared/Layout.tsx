import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'

export default function Layout() {
  return (
    <div className="layout">
      <Sidebar />
      <div className="main-content">
        <div className="page fade-in">
          <Outlet />
        </div>
      </div>
    </div>
  )
}
