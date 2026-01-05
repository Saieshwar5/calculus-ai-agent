




export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (



        <div className="flex flex-col min-h-screen items-center justify-center bg-gray-100">

           <div className="flex flex-col justify-center items-center bg-white shadow-md rounded-lg p-8 w-full max-w-md">

              { children}
           </div>
            
        </div>
         
        
        
      
  );
}