import './styles.css';

export default function ErrorMessage({ message }) {

    return (
        <>
            <div className='error-message'>
                <h4>{message}</h4>
            </div>
        </>
    );
}