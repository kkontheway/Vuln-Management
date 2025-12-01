import IPExtractBox from '../components/ChatBox/IPExtractBox';
import RecommendationGenerator from '../components/Recommendation/RecommendationGenerator';

const Tools = () => {
  return (
    <div className="space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-semibold text-text-primary mb-2">Tools</h1>
        <p className="text-text-secondary">Utility tools for security operations</p>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <div>
          <IPExtractBox />
        </div>
        <div>
          <RecommendationGenerator />
        </div>
      </div>
    </div>
  );
};

export default Tools;
