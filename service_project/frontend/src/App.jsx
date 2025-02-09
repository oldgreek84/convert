function App() {
    const apiUrl = import.meta.env.VITE_BACKEND_URL
    let resM = {};
    const msg = "message";

    let fetchData = () => {

        console.log("some")
        fetch(`${apiUrl}/api`).then((res) => {

            // console.log(res)
            console.log("in fetch")
            resM.s = res.body.message
            console.log("in fetch", res)
            console.log("in fetch", res.json().body)
            // console.log("in fetch", res.json().then((res) => {console.log("json: ", res)}))
        }).catch((er) => { console.log(er) })
    };

    return (
        <>
            <div className='flex-row center m-2'>
                <div className='border-red-50 mb-4'>
                    <button className='p-2 border-2 border-sky-500 rounded-md' onClick={fetchData}>Some new</button>
                </div>
                <div className='border-red-300 bg-red-300 p-4'>
                    <span className='font-medium'>Hello World! {resM.message} {msg}</span>
                </div>
            </div>
        </>
    )
}

export default App
