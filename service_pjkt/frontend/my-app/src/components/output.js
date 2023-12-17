import React, {useRef, useEffect} from "react";

const Output = ({children}) => {
  const refBox = useRef(null)
  useEffect(() => {
    const elBox = refBox.current
    if (elBox) {
      elBox.scrollTop = elBox.scrollHight
    }
  }, [children])

  return (
    <div ref={refBox} style={styles.container} className="container text mt-5">
      <pre>{children}</pre>
    </div>
  );
};

const styles = {
  container: {
    flex: 1,
    color: 'red',
  }
}

export default Output;
