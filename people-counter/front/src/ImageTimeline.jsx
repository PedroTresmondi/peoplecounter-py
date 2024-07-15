import React, { useEffect, useState } from 'react';
import { supabase } from './supabase';
import './App.css'; // Certifique-se de importar o arquivo CSS onde estão os estilos

const ImageSlider = () => {
    const [images, setImages] = useState([]);
    const [currentIndex, setCurrentIndex] = useState(0);

    useEffect(() => {
        const fetchImages = async () => {
            console.log('Fetching images...');
            const { data, error } = await supabase.storage.from('heatmap').list('heatmaps');
            if (error) {
                console.error('Error fetching images:', error);
                return;
            }
            console.log('Data fetched:', data);

            const imageUrls = data.map(img => {
                if (img.name === '.emptyFolderPlaceholder') return null;
                const { data: publicUrlData, error } = supabase.storage.from('heatmap').getPublicUrl(`heatmaps/${img.name}`);
                console.log(`Response from getPublicUrl for ${img.name}:`, { publicUrlData, error });
                if (error) {
                    console.error(`Error getting public URL for ${img.name}:`, error);
                    return null;
                }
                console.log(`Public URL for ${img.name}:`, publicUrlData.publicUrl);
                return publicUrlData.publicUrl;
            }).filter(url => url !== null);
            console.log('Image URLs:', imageUrls);
            setImages(imageUrls);
        };

        fetchImages();
        const interval = setInterval(fetchImages, 10000);

        return () => clearInterval(interval);
    }, []);

    const handleSliderChange = (event) => {
        setCurrentIndex(parseInt(event.target.value));
    };

    return (
        <div className="slider">
            <h1>Image Slider</h1>
            {images.length === 0 ? (
                <p>No images found</p>
            ) : (
                <div className="slider-container">
                    <div className="image-container">
                        <img src={images[currentIndex]} alt={`image-${currentIndex}`} className="slider-image" />
                    </div>
                    <input
                        type="range"
                        min="0"
                        max={images.length - 1}
                        value={currentIndex}
                        onChange={handleSliderChange}
                        className="slider-bar"
                    />
                </div>
            )}
        </div>
    );
};

export default ImageSlider;
