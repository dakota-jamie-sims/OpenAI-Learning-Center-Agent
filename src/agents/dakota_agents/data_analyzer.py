"""Dakota Data Analyzer Agent - Analyzes spreadsheet data for insights"""

import os
import json
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from datetime import datetime

from .base_agent import DakotaBaseAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaDataAnalyzer(DakotaBaseAgent):
    """Analyzes spreadsheet data and extracts insights for articles"""
    
    def __init__(self):
        super().__init__("data_analyzer", model_override="gpt-5")
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze spreadsheet data and extract insights"""
        try:
            self.update_status("active", "Analyzing spreadsheet data")
            
            data_file = task.get("data_file")
            topic = task.get("topic", "")
            analysis_type = task.get("analysis_type", "general")  # general, performance, trends, comparison
            
            if not data_file or not os.path.exists(data_file):
                self.logger.info("No data file provided, skipping data analysis")
                return self.format_response(True, data={
                    "insights": [],
                    "metrics": {},
                    "charts_data": {},
                    "key_findings": []
                })
            
            # Read the data
            df = self._read_data_file(data_file)
            if df is None:
                return self.format_response(False, error=f"Failed to read data file: {data_file}")
            
            self.logger.info(f"Loaded data with shape: {df.shape}")
            
            # Perform basic analysis
            basic_stats = self._get_basic_statistics(df)
            
            # Get AI-powered insights
            insights = await self._generate_insights(df, topic, analysis_type)
            
            # Extract key metrics
            key_metrics = self._extract_key_metrics(df, analysis_type)
            
            # Prepare data for potential charts
            charts_data = self._prepare_chart_data(df, analysis_type)
            
            # Format key findings
            key_findings = self._format_key_findings(insights, key_metrics)
            
            return self.format_response(True, data={
                "insights": insights,
                "metrics": key_metrics,
                "basic_stats": basic_stats,
                "charts_data": charts_data,
                "key_findings": key_findings,
                "data_source": os.path.basename(data_file),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist()
            })
            
        except Exception as e:
            self.logger.error(f"Data analysis error: {e}")
            return self.format_response(False, error=str(e))
    
    def _read_data_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Read data from Excel or CSV file"""
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                # Try to read the first sheet with data
                df = pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                # Try different encodings
                try:
                    df = pd.read_csv(file_path)
                except:
                    df = pd.read_csv(file_path, encoding='latin1')
            else:
                self.logger.error(f"Unsupported file format: {file_path}")
                return None
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def _get_basic_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get basic statistics from the dataframe"""
        stats = {}
        
        # Numeric columns statistics
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            stats["numeric_summary"] = df[numeric_cols].describe().to_dict()
        
        # Date columns
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        if date_cols:
            stats["date_range"] = {}
            for col in date_cols:
                stats["date_range"][col] = {
                    "min": str(df[col].min()),
                    "max": str(df[col].max())
                }
        
        # Categorical columns
        object_cols = df.select_dtypes(include=['object']).columns.tolist()
        if object_cols:
            stats["categorical_summary"] = {}
            for col in object_cols[:5]:  # Limit to first 5 to avoid too much data
                value_counts = df[col].value_counts().head(10)
                stats["categorical_summary"][col] = value_counts.to_dict()
        
        return stats
    
    async def _generate_insights(self, df: pd.DataFrame, topic: str, analysis_type: str) -> List[str]:
        """Use GPT-5 to generate insights from the data"""
        
        # Prepare data sample for analysis
        data_summary = self._prepare_data_summary(df)
        
        prompt = f"""Analyze this dataset related to '{topic}' and provide key insights for institutional investors.

Analysis Type: {analysis_type}

Dataset Overview:
- Shape: {df.shape[0]} rows, {df.shape[1]} columns
- Columns: {', '.join(df.columns.tolist())}

Data Sample (first 10 rows):
{df.head(10).to_string()}

Summary Statistics:
{data_summary}

Based on this data, provide 5-7 specific, quantitative insights that would be valuable for institutional investors. Focus on:
1. Key trends and patterns
2. Notable outliers or anomalies
3. Performance metrics and comparisons
4. Risk indicators
5. Investment implications

Format each insight as a complete sentence with specific numbers where applicable."""

        try:
            insights_text = await self.query_llm(prompt, max_tokens=800)
            
            # Parse insights into a list
            insights = []
            for line in insights_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Clean up numbering and bullets
                    insight = line.lstrip('0123456789.-•').strip()
                    if insight:
                        insights.append(insight)
            
            return insights[:7]  # Limit to 7 insights
            
        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return ["Data analysis completed but insights generation failed"]
    
    def _prepare_data_summary(self, df: pd.DataFrame) -> str:
        """Prepare a concise summary of the data for GPT analysis"""
        summary_parts = []
        
        # Numeric summary
        numeric_df = df.select_dtypes(include=[np.number])
        if not numeric_df.empty:
            summary_parts.append("Numeric Summary:")
            summary_parts.append(numeric_df.describe().to_string())
        
        # Missing data
        missing = df.isnull().sum()
        if missing.any():
            summary_parts.append("\nMissing Data:")
            summary_parts.append(missing[missing > 0].to_string())
        
        return '\n'.join(summary_parts)
    
    def _extract_key_metrics(self, df: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """Extract key metrics based on analysis type"""
        metrics = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if analysis_type == "performance" and numeric_cols:
            # Look for return/performance columns
            perf_cols = [col for col in numeric_cols if any(
                keyword in col.lower() for keyword in ['return', 'performance', 'gain', 'loss', 'pnl']
            )]
            
            for col in perf_cols[:3]:  # Limit to top 3
                metrics[col] = {
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std()),
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "median": float(df[col].median())
                }
        
        elif analysis_type == "trends" and numeric_cols:
            # Calculate growth rates if possible
            for col in numeric_cols[:3]:
                if len(df) > 1:
                    metrics[f"{col}_change"] = {
                        "total_change": float(df[col].iloc[-1] - df[col].iloc[0]),
                        "percent_change": float((df[col].iloc[-1] - df[col].iloc[0]) / df[col].iloc[0] * 100) if df[col].iloc[0] != 0 else 0
                    }
        
        else:
            # General metrics
            for col in numeric_cols[:5]:
                metrics[col] = {
                    "mean": float(df[col].mean()),
                    "median": float(df[col].median()),
                    "std": float(df[col].std())
                }
        
        return metrics
    
    def _prepare_chart_data(self, df: pd.DataFrame, analysis_type: str) -> Dict[str, Any]:
        """Prepare data that could be used for charts"""
        charts = {}
        
        # Time series data
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if date_cols and numeric_cols:
            # Prepare time series data
            date_col = date_cols[0]
            value_col = numeric_cols[0]
            
            time_series = df[[date_col, value_col]].dropna()
            if len(time_series) > 0:
                charts["time_series"] = {
                    "x": time_series[date_col].astype(str).tolist(),
                    "y": time_series[value_col].tolist(),
                    "x_label": date_col,
                    "y_label": value_col
                }
        
        # Distribution data
        if numeric_cols:
            col = numeric_cols[0]
            charts["distribution"] = {
                "values": df[col].dropna().tolist()[:100],  # Limit to 100 points
                "label": col
            }
        
        return charts
    
    def _format_key_findings(self, insights: List[str], metrics: Dict[str, Any]) -> List[str]:
        """Format the most important findings for the article"""
        findings = []
        
        # Add top insights
        for insight in insights[:3]:
            findings.append(insight)
        
        # Add key metric highlights
        for metric_name, values in list(metrics.items())[:2]:
            if isinstance(values, dict) and 'mean' in values:
                finding = f"{metric_name.replace('_', ' ').title()} averaged {values['mean']:.2f}"
                if 'std' in values:
                    finding += f" with volatility of {values['std']:.2f}"
                findings.append(finding)
        
        return findings