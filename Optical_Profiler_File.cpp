#include "Optical_Profiler_File.h"

#include <regex>
#include <memory>
#include <string>

using namespace std;
using namespace cv;

bool Optical_Profiler_File::Open( const char* file_name )
{
	ifstream optical_profiler_file( file_name, std::ios_base::binary );
	if( !optical_profiler_file.is_open() )
		return false;

	long begin = optical_profiler_file.tellg();
	optical_profiler_file.seekg( 0, ios::end );
	long end = optical_profiler_file.tellg();
	optical_profiler_file.seekg( ios::beg );
	long file_size = end - begin;

	if( file_size < 0x324 )
		return false;

	int rows;
	optical_profiler_file.seekg( 0x31C );
	optical_profiler_file.read( (char*)&rows, 4 );
	int columns;
	optical_profiler_file.seekg( 0x320 );
	optical_profiler_file.read( (char*)&columns, 4 );

	if( rows * columns * sizeof( float ) + 0x324 > file_size )
		return false;

	int image_is_here = 0x324;
	if( !Read_Header_Info( optical_profiler_file, 0, 0x324 ) )
	{
		if( !Read_Header_Info( optical_profiler_file, 0x324 + rows * columns * sizeof( float ), 0x310 ) )
			return false;
		image_is_here = 0x324 + rows * columns * sizeof( float ) + 0x310;
	}
	this->_heightmap_image = Mat( rows, columns, CV_32F );

	optical_profiler_file.seekg( image_is_here );
	//optical_profiler_file.seekg( 0x12C634 );
	optical_profiler_file.read( (char*)this->_heightmap_image.data, rows * columns * sizeof( float ) );
	int possible_second_image = 0x324 + rows * columns * sizeof( float ) + 0x310;
	int testing_thing2 = 0x324 + 2 * rows * columns * sizeof( float );

	return true;
}

bool Optical_Profiler_File::Read_Header_Info( std::ifstream & optical_profiler_file, int start_location, int size )
{
	optical_profiler_file.seekg( start_location );
	vector<char> header_data( size );
	optical_profiler_file.read( header_data.data(), size );

	double z_scale = 0;
	double actual_width_extent = 0;
	double actual_height_extent = 0;
	int num_x_points = 0;
	int num_y_points = 0;

	string x_units;
	string y_units;
	string z_units;

	bool correct_image = false;

	auto get_units = []( const char* scale_string )
	{
		if( 0 == strncmp( scale_string, "Millimeter", strlen( "Millimeter" ) ) )
			return "Millimeter";
		if( 0 == strncmp( scale_string, "Micrometer", strlen( "Micrometer" ) ) )
			return "Micrometer";
		if( 0 == strncmp( scale_string, "Nanometer", strlen( "Nanometer" ) ) )
			return "Nanometer";

		return "";
	};

	for( int i = 0; i < size; i++ )
	{
		switch( header_data[ i ] ) // To prevent a ton of string compares, only check if the first letter is correct
		{
			case 'D':
			if( 0 == strncmp( &header_data[ i ], "Dimension1Points", strlen( "Dimension1Points" ) ) )
			{
				num_x_points = *((int*)&header_data[ i + strlen( "Dimension1Points" ) + 1 ]);
			}
			if( 0 == strncmp( &header_data[ i ], "Dimension2Points", strlen( "Dimension2Points" ) ) )
			{
				num_y_points = *((int*)&header_data[ i + strlen( "Dimension2Points" ) + 1 ]);
			}
			if( 0 == strncmp( &header_data[ i ], "Dimension1Extent", strlen( "Dimension1Extent" ) ) )
			{
				actual_width_extent = *((double*)&header_data[ i + strlen( "Dimension1Extent" ) + 3 ]);
				char* width_units_as_chars = &header_data[ i + strlen( "Dimension1Extent" ) + 3 + 12 ];
				x_units = get_units( width_units_as_chars );
			}
			if( 0 == strncmp( &header_data[ i ], "Dimension2Extent", strlen( "Dimension2Extent" ) ) )
			{
				actual_height_extent = *((double*)&header_data[ i + strlen( "Dimension2Extent" ) + 3 ]);
				char* height_units_as_chars = &header_data[ i + strlen( "Dimension2Extent" ) + 3 + 12 ];
				y_units = get_units( height_units_as_chars );
			}
			if( 0 == strncmp( &header_data[ i ], "DataScale", strlen( "DataScale" ) ) )
			{
				z_scale = *((double*)&header_data[ i + strlen( "DataScale" ) + 3 ]);
				char* z_units_as_chars = &header_data[ i + strlen( "DataScale" ) + 15 ];
				z_units = get_units( z_units_as_chars );
			}
			else if( 0 == strncmp( "DataKind", &header_data[ i ], strlen( "DataKind" ) ) &&
				0 == strncmp( "Height", &header_data[ i + strlen( "DataKind" ) + 3 ], strlen( "Height" ) ) )
			{
				correct_image = true;
			}
			break;
			default:
			break;
		}
	}

	if( !correct_image || actual_width_extent == 0 || actual_height_extent == 0 || z_scale == 0 || num_x_points == 0 || num_y_points == 0 )
		return false;

	this->_x_units = x_units;
	this->_y_units = y_units;
	this->_z_units = z_units;
	this->_x_scale = actual_width_extent / (num_x_points - 1);
	this->_y_scale = actual_height_extent / (num_y_points - 1);
	this->_z_scale = z_scale;

	return true;
}
