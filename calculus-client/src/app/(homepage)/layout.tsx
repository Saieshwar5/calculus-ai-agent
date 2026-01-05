"use client";
import { useState } from "react";
import styles from "./mainLayout.module.css";
import LeftSideBar1 from "../components/leftSidebar/leftSidebar1";
import ProfileModal from "../components/modals/ProfileModal";


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {


  const [expanded, setExpanded] = useState(false);
  const [isProfileModalOpen, setIsProfileModalOpen] = useState(false);
  const changeSidebarState = () => {
    setExpanded(!expanded);
  }

  const handleProfileClick = () => {
    setIsProfileModalOpen(true)
  }

  return (
    <div
      className={styles.mainLayout}
    >
      
        <aside className={expanded ? styles.leftSidebarExpanded : styles.leftSidebar}>
          <LeftSideBar1 changeSidebarState={changeSidebarState} expanded={expanded} onProfileClick={handleProfileClick}/>
      </aside>

      <main 
        className={styles.mainContent}
        style={{
          marginLeft: expanded ? '320px' : '120px',
          width: expanded ? 'calc(100vw - 320px)' : 'calc(100vw - 120px)',
        }}
      >
        {children}
      </main>

      <ProfileModal isOpen={isProfileModalOpen} onClose={() => setIsProfileModalOpen(false)}/>

      
    </div>
  );
}
